#!/usr/bin/env python3

import requests
import json
import subprocess
from sys import exit
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-o', '--organization',\
        help='Github organization', required=True)

parser.add_argument('-r', '--repo',\
        help='Github repo', required=True)

parser.add_argument('-v', '--version-tag', default='latest',\
        help='Release version or tag', metavar='version_tag')

parser.add_argument('-t', '--token',\
        help='Github token', required=True)

parser.add_argument('-d', '--deploy-path', required=False,\
        help='Deploy asset path',  metavar='deploy_path')

parser.add_argument('-p', '--post-exec',\
        help='Post exec command', required=False)

parser.add_argument('-z', '--unzip',\
        help='Unzip asset', action='store_true', required=False)

parser.add_argument('-tp', '--tmp-path',\
        help='Temp path for asset', default='/tmp', required=False, metavar='tmp_path')

parser.add_argument('-an', '--asset-name',\
        help='Name of the asset you want to download', required=False, metavar='asset_name')

args = parser.parse_args()

org = args.organization
repo = args.repo
token = args.token
path = args.deploy_path
version_tag = args.version_tag
post_exec_cmd = args.post_exec
unzip = args.unzip
tmp_path = args.tmp_path
an = args.asset_name

env_vars = {}

def download_asset(asset):
    print("download")
    zip_path = tmp_path + "/release.zip"
    try:
        subprocess.run(['/bin/mkdir', '-p', tmp_path], check=True)
        subprocess.run(['/usr/bin/wget', '--header', 'Accept: application/octet-stream','--header','Authorization: token %s' % token, asset, '-O', zip_path, '-nv'], check=True)
        env_vars["name"] = asset
        env_vars["version"] = version_tag
        env_vars["path"] = tmp_path
    except Exception as e:
        print(e)
        exit(1)
        
def unzip_asset(path):
    release_tmp_path = tmp_path + "/release"
    zip_path = tmp_path + "/release.zip"
    assets_path = path + "/assets"
    try:
        subprocess.run(['/bin/rm', '-rf', release_tmp_path], check=True)
        subprocess.run(['/bin/mkdir', '-p', release_tmp_path], check=True)
        subprocess.run(['/bin/mkdir', '-p', assets_path], check=True)
        subprocess.run(['/usr/bin/unzip', '-o', zip_path, '-d', release_tmp_path], check=True)
        subprocess.run(['/usr/bin/rsync', '-aHvxr', '--delete', release_tmp_path + "/", assets_path ], check=True)
        subprocess.run(['/bin/rm', '-rf', zip_path], check=True)
        subprocess.run(['/bin/rm', '-rf', release_tmp_path], check=True)
        env_vars["path"] = path
    except Exception as e:
        print(e)
        exit(1)

def post_exec(cmd):
    print("post exec")
    try:
        subprocess.run(cmd, env=env_vars, shell=True, check=True)
    except Exception as e:
        print(e)
        exit(1)

try:
    url = 'https://api.github.com/repos/{}/{}/releases/{}'.format(org, repo, version_tag)
    headers = {'Authorization': 'token %s' % token}
    response = requests.get(url,headers=headers).json()

    #print(response.json())

    tag = response['tag_name']

    # get a specific asset, or get the first one by default
    assets = response['assets']
    asset = response['assets'][0]['url']
    if an:
        for asset_obj in assets:
            if asset_obj['name'] == an:
                asset = asset_obj['url']

    new_release = { 'tag': tag, 'asset': asset }
    print(tag,asset)

except Exception as e:
    print("Could not get github asset: ", e)
    exit(1)


try:
    release_file = open(path + '/release.txt', 'r+')
    current_release = json.load(release_file)
    release_file.close()
except:
    current_release = { 'tag': '' }
if new_release['tag'] != current_release['tag']:
    download_asset(new_release['asset'])
    if unzip and path:
        unzip_asset(path)
    if post_exec_cmd:
        post_exec(post_exec_cmd)
    release_file = open(path + '/release.txt', 'w')
    json.dump(new_release,release_file)

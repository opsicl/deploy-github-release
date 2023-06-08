#!/usr/bin/env python3

import requests
import json
import subprocess
from sys import exit
import argparse
import os

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
        help='Github token',  metavar='deploy_path')

parser.add_argument('-p', '--post-exec',\
        help='Post exec command', required=False)

parser.add_argument('-z', '--unzip',\
        help='Unzip asset', default=True, required=False)


args = parser.parse_args()

org = args.organization
repo = args.repo
token = args.token
path = args.deploy_path
version_tag = args.version_tag
post_exec_cmd = args.post_exec
unzip = args.unzip

env_vars = {}

def download_asset(asset):
    try:
        subprocess.run(['/usr/bin/wget', '--header', 'Accept: application/octet-stream','--header','Authorization: token %s' % token, asset, '-O', '/tmp/release.zip', '-nv'])
        env_vars["name"] = asset
        env_vars["version"] = version_tag
    except Exception as e:
        print(e)
        exit(1)
        
def unzip_asset(path):
    try:
        subprocess.run(['/bin/rm', '-rf', '/tmp/release'])
        subprocess.run(['/bin/mkdir', '-p', '/tmp/release'])
        subprocess.run(['/usr/bin/unzip', '-o', '/tmp/release.zip', '-d', '/tmp/release'])
        subprocess.run(['/usr/bin/rsync', '-aHvxr', '--delete', '/tmp/release/', path ])
        subprocess.run(['/bin/rm', '-rf', '/tmp/release.zip'])
        subprocess.run(['/bin/rm', '-rf', '/tmp/release'])
        env_vars["path"] = path
    except Exception as e:
        print(e)
        exit(1) 

def post_exec(cmd):
    try:
        subprocess.run(cmd, env=env_vars, shell=True)
    except Exception as e:
        print(e)
        exit(1)

url = 'https://api.github.com/repos/{}/{}/releases/{}'.format(org, repo, version_tag)
headers = {'Authorization': 'token %s' % token}
response = requests.get(url,headers=headers).json()

#print(response.json())

tag = response['tag_name']
asset = response['assets'][0]['url']
new_release = { 'tag': tag, 'asset': asset }
print(tag,asset)


try:
    release_file = open(path + '/release.txt', 'r+')
    current_release = json.load(release_file)
    release_file.close()
except:
    current_release = { 'tag': '' }
if new_release['tag'] != current_release['tag']:
    download_asset(new_release['asset'])
    if unzip and path:
        unzip_asset(asset)
    if post_exec_cmd:
        post_exec(post_exec_cmd)
    release_file = open(path + '/release.txt', 'w')
    json.dump(new_release,release_file)

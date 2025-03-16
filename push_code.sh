#!/bin/bash
# simple script to push code to both gitlab origin and backup which is
# forgejo server code.rovitotv.org

git push
git push backup main

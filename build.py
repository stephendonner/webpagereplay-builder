#!/usr/bin/env python
# Copyright (c) 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import shutil
import sys
import subprocess
import tempfile
import platform

TELEMETRY_DIR = os.path.join('/root/go/src/github.com/catapult-project/catapult/telemetry')
sys.path.insert(1, TELEMETRY_DIR)
from telemetry.core import util
from telemetry.core import platform as platform_module
from telemetry.internal.util import binary_manager

import py_utils


_WPR_GO_DIR = os.path.join(util.GetCatapultDir(), 'web_page_replay_go', 'src')


_SUPPORTED_GO_VERSIONS = ('go1.8', 'go1.9')


def check_go_version():
  try:
    out = subprocess.check_output(['go', 'version'])
  except subprocess.CalledProcessError:
    out = 'no go binary found'
  assert any(v in out for v in _SUPPORTED_GO_VERSIONS), (
      'Require go version 1.8 or higher. Found: %s' % out)


def build_wpr_go(os_name, os_arch):
  """ Build and return path to wpr binary."""
  # go build command recognizes 'amd64' but not 'x86_64', so we switch 'x86_64'
  # to 'amd64' string here.
  # The two names can be used interchangbly, see:
  # https://wiki.debian.org/DebianAMD64Faq?action=recall&rev=65
  if os_arch == 'x86_64' or os_arch == 'AMD64':
    os_arch = 'amd64'

  if os_arch == 'x86':
    os_arch = '386'

  if os_arch == 'armv7l':
    os_arch = 'arm'

  if os_arch == 'aarch64':
    os_arch = 'arm64'

  if os_arch == 'mipsel':
    os_arch = 'mipsle'

  # go build command recognizes 'darwin' but not 'mac'.
  if os_name == 'mac':
    os_name = 'darwin'

  if os_name == 'win':
    os_name = 'windows'

  check_go_version()

  try:
    # We want to build wpr from the local source. We do this by
    # making a temporary GOPATH that symlinks to our local directory.
    go_path_dir = tempfile.mkdtemp()
    repo_dir = os.path.join(go_path_dir, 'src/github.com/catapult-project')
    os.makedirs(repo_dir)
    os.symlink(util.GetCatapultDir(), os.path.join(repo_dir, 'catapult'))

    env = os.environ.copy()
    env['GOPATH'] = go_path_dir
    env['GOOS'] = os_name
    env['GOARCH'] = os_arch
    env['CGO_ENABLED'] = '0'

    print 'GOPATH=%s' % go_path_dir
    print 'CWD=%s' % _WPR_GO_DIR

    get_cmd = ['go', 'get', '-d', './...']
    print 'Running get command: %s' % ' '.join(get_cmd)
    subprocess.check_call(get_cmd, env=env, cwd=_WPR_GO_DIR)

    build_cmd = ['go', 'build', '-v', 'wpr.go']
    print 'Running build command: %s' % ' '.join(build_cmd)
    subprocess.check_call(build_cmd, env=env, cwd=_WPR_GO_DIR)

    cp_cmd = ['cp', 'wpr', '/output/']	
    subprocess.check_call(cp_cmd, env=env, cwd=_WPR_GO_DIR)
	
  finally:
   if go_path_dir:
     shutil.rmtree(go_path_dir)

  if os_name == 'windows':
    return os.path.join(_WPR_GO_DIR, 'wpr.exe')
  return os.path.join(_WPR_GO_DIR, 'wpr')


# TODO(nedn): support building other architectures & OSes.
_SUPPORTED_PLATFORMS = (
#  ('win', 'x86'),
#  ('mac', 'x86_64'),
  ('linux', 'x86_64'),
#  ('win', 'AMD64'),
#  ('linux', 'armv7l'),
#  ('linux', 'aarch64'),
#  ('linux', 'mipsel')
)


def get_latest_wpr_go_commit_hash():
  return subprocess.check_output(
    ['git', 'log', '-n', '1', '--pretty=format:%H', _WPR_GO_DIR]).strip()


def BuildAndUpdateWPRGoBinary(os_name, arch_name):
  if (os_name, arch_name) not in _SUPPORTED_PLATFORMS:
    raise NotImplementedError('OS = %s, ARCH = %s is not supported' %
        (os_name, arch_name))

  print 'Build WPR binary for OS %s, ARCH: %s' % (os_name, arch_name)
  wpr_bin = build_wpr_go(os_name, arch_name)

def main():
  for os_name, arch_name in _SUPPORTED_PLATFORMS:
    BuildAndUpdateWPRGoBinary(os_name, arch_name)


if __name__ == "__main__":
  sys.exit(main())

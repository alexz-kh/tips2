#!/bin/bash
set -x

o_filter='-filter="Name (~ .*salt-formula-linux)|Name (~ .*salt-formula-m.*)"'
repo_key='http://mirror.mirantis.com/nightly/salt-formulas/xenial/archive-salt-formulas.key'
repo_url='http://mirror.mirantis.com/nightly/salt-formulas/xenial'
repo_Dist='xenial'
repo_components='main'

#[ -z "${repoName}" ] && exit 1
#[ -z "${repoDist}" ] && exit 1
#[ -z "${repoComponent}" ] && exit 1

aptlyArchs=${aptlyArchs:-"amd64"}
repoDist=${repo_Dist}
repoComponent=main
repoOrigin=superOrig
repoName=superlabel

tempMirName=${RANDOM}
temoRepoName=${RANDOM}

# ==== body ================
rm -rf result
# Renew aptly config
cat > "aptly.conf" <<EOF
{
  "rootDir": "/var/lib/aptly",
  "downloadConcurrency": 6,
  "downloadSpeedLimit": 0,
  "architectures": [],
  "dependencyFollowSuggests": false,
  "dependencyFollowRecommends": false,
  "dependencyFollowAllVariants": false,
  "dependencyFollowSource": false,
  "gpgDisableSign": true,
  "gpgDisableVerify": true,
  "downloadSourcePackages": false,
  "ppaDistributorID": "ubuntu",
  "ppaCodename": "",
  "skipContentsPublishing": false,
  "S3PublishEndpoints": {},
  "SwiftPublishEndpoints": {}
}
EOF

cat > "task.sh" <<EOF
#!/bin/bash
set -ex
#wget -O - ${repo_key} | gpg --no-default-keyring --keyring trustedkeys.gpg --import
aptly mirror create ${tempMirName} ${repo_url} ${repo_Dist} ${repo_components}
aptly mirror edit ${o_filter} ${tempMirName}
aptly mirror update ${tempMirName}

aptly snapshot create ${temoRepoName} from mirror ${tempMirName}

aptly publish snapshot \
    --architectures "${aptlyArchs}" \
    --distribution "${repoDist}" \
    --component "${repoComponent}" \
    --origin ${repoOrigin} \
    --label "${repoName}" \
    ${temoRepoName}

sleep 99h || true
EOF
chmod 0755 task.sh

dname=aptly_test
volumes="-v $(pwd)/task.sh:/task.sh:ro -v $(pwd)/result/:/var/lib/aptly -v $(pwd)/aptly.conf:/etc/aptly.conf:ro"
opts="--rm $volumes --name ${dname}"
docker stop --name ${dname} || true
docker rm -f ${dname} || true
docker run --entrypoint=/task.sh ${opts} docker-prod-local.artifactory.mirantis.com/mirantis/cicd/aptly-api:2018.11.0

def dockerRepoName      = 'm3-core'
def serviceName         = 'm3-core'
def repoServiceName     = 'github.com'
def repoName            = "git@${repoServiceName}:legoly/${serviceName}.git"
def infrastructureRepoName = "git@${repoServiceName}:legoly/infrastructure.git"
def err                 = null
def awsRegion           = 'us-east-1'
def awsClientId         = "682989504111"
def dockerRegistryName  = "${awsClientId}.dkr.ecr.${awsRegion}.amazonaws.com"
def dockerRegistryUrl   = "https://${dockerRegistryName}"
def fileVersion         = "${serviceName}-build-name.txt"
def slackTeam           = 'teammagia'
def infrastructurePath  = "infrastructure"
currentBuild.result     = 'SUCCESS'

def deploy_app(environment, svcName, dockerTag, awsRegion, homeDir) {
    dir("${homeDir}") {
        withEnv(["SERVICE_NAME=${svcName}",
                 "SERVICE_DOCKER_TAG=${dockerTag}",
                 "AWS_REGION=${awsRegion}",
                 "AWS_DEFAULT_REGION=${awsRegion}",
                 "ENVIRONMENT=${environment}"]) {
            sh '''
                ./jenkins/deploy-service/update-service.sh \
                    --name $SERVICE_NAME \
                    --tag $SERVICE_DOCKER_TAG \
                    --env $ENVIRONMENT
            '''
        }
    }
}

// To use slack notifications install Jenkins CI Slack App
// https://{{ SLACK_TEAM }}.slack.com/apps/A0F7VRFKN-jenkins-ci
def buildNotify(slackTeam, buildStatus, subject) {
    // build status of null means successful
    buildStatus =  buildStatus ?: 'SUCCESS'

    // Default values
    def colorCode = 'warning'
    def summary = "${subject} (<${env.BUILD_URL}|Open>)"

    // Override default values based on build status
    if (buildStatus == 'STARTED') {
      colorCode = 'warning'
    } else if (buildStatus == 'SUCCESS') {
      colorCode = 'good'
    } else {
      colorCode = 'danger'
    }

    // Send notifications
    slackSend color: colorCode,
              message: summary,
              teamDomain: "${slackTeam}",
              channel: '#jenkins',
              tokenCredentialId: 'slack-token'
}

//   properties([
//           pipelineTriggers([pollSCM('H/2 * * * *')]),
//           disableConcurrentBuilds()
//    ])
properties([])

    try {
        stage('Get Source') {
            // Do not clean workspace to prevent rebuilding python libs
         node {
            checkout([
                $class: 'GitSCM',
                branches: [[name: '*/master']],
                doGenerateSubmoduleConfigurations: false,
                extensions: [[$class: 'CleanCheckout'], [
                $class: 'SubmoduleOption',
                disableSubmodules: false,
                parentCredentials: true,
                recursiveSubmodules: true,
                reference: '',
                trackingSubmodules: false
                ]],
                submoduleCfg: [],
                userRemoteConfigs: [[credentialsId: 'mykola-github-key', url: "${repoName}"]]
            ])

            // Change build display name
            gitCommit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
            shortCommit = gitCommit.take(7)

            currentBuild.displayName = "${BUILD_NUMBER}-${shortCommit}"

            gitCommitAuthor = sh(returnStdout: true, script: 'git show --format="%aN" ${gitCommit} | head -1').trim()

            buildNotify "${slackTeam}", 'STARTED', "${env.JOB_NAME} - ${currentBuild.displayName} Started by changes from ${gitCommitAuthor}"

            writeFile file: "${fileVersion}", text: "${currentBuild.displayName}"

            dir("${infrastructurePath}") {
                git url: "${infrastructureRepoName}", changelog: false, credentialsId: 'mykola-github-key', poll: false
            }
        }
       }


        stage('Build and Publish Docker Image') {
            node {
                docker.withRegistry("${dockerRegistryUrl}") {
                def image = docker.build("${dockerRepoName}:${currentBuild.displayName}")
                image.push()
                image.push 'latest'
                }
            }
        }

        stage('Deploy to DEV') {
        if ( env.BRANCH_NAME == "master") {
            node {
                lock(resource: "deploy-${serviceName}-to-v2-dev", inversePrecedence: true) {
                    milestone 1
                    echo "[INFO] Deploying to Dev"
                    deploy_app "v2-dev", "${serviceName}", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
                    deploy_app "v2-dev", "${serviceName}-beat", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
                    deploy_app "v2-dev", "${serviceName}-worker", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
                    deploy_app "v2-dev", "${serviceName}-flower", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
                }
                buildNotify "${slackTeam}", "SUCCESS", "[SUCCESS] ${env.JOB_NAME}: Deploy to DEV: ${currentBuild.displayName}"
            }
        }
    }
    stage('Deploy to PROD'){
      input message: "Deploy to Production?"
      node {
          lock(resource: "deploy-${serviceName}-to-prod_m3", inversePrecedence: true) {
              milestone 2
              echo "[INFO] Deploying to Production"
              deploy_app "prod_m3", "${serviceName}", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
              deploy_app "prod_m3", "${serviceName}-beat", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
              deploy_app "prod_m3", "${serviceName}-worker", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
              deploy_app "prod_m3", "${serviceName}-flower", "${currentBuild.displayName}", "${awsRegion}", "${infrastructurePath}"
          }
          buildNotify "${slackTeam}", "SUCCESS", "[SUCCESS] ${env.JOB_NAME}: Deploy to PROD: ${currentBuild.displayName}"
      }
    }

    }
    catch (caughtError) {
        currentBuild.result = "FAILURE"
        throw caughtError
    }
    finally {
        node {
        buildNotify "${slackTeam}", "${currentBuild.result}", "${env.JOB_NAME} - ${currentBuild.displayName} ${currentBuild.result}"

        // Remove docker images from jenkins
        sh """
            [ -z "\$(docker images -q ${dockerRegistryName}/${dockerRepoName}:${currentBuild.displayName})" ] || docker rmi "${dockerRegistryName}/${serviceName}:${currentBuild.displayName}"
            [ -z "\$(docker images -q ${dockerRegistryName}/${dockerRepoName}:latest)" ] || docker rmi "${dockerRegistryName}/${serviceName}:latest"
            [ -z "\$(docker images -q ${dockerRepoName}:${currentBuild.displayName})" ] || docker rmi "${serviceName}:${currentBuild.displayName}"
        """

        archiveArtifacts artifacts: "${fileVersion}",
                         onlyIfSuccessful: true
        }
    }


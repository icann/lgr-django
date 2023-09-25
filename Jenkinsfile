@Library('ICANN_LIB') _
utils = new icann.Utilities()

properties([[$class: 'BuildDiscarderProperty', strategy: [$class: 'LogRotator', artifactDaysToKeepStr: '14', artifactNumToKeepStr: '10', daysToKeepStr: '14', numToKeepStr: '10']]])

node('okd-jenkins-build-lax-docker') {

    gitscm = null

    try {
        stage('Checkout on Slave') {
            // utils.sendNotification(slackChannel: 'jenkinsjobs', sendSlackMessage: true, buildStatus: 'STARTED')
            gitScm = checkout scm
        }

        stage('Build and Push HTTPD Proxy') {
           //TODO: Remove once deployment script are tested
           // if (!utils.hasFolderChanged("src")) {
           //     echo "No changes. No new httpd image to publish"
           //     return;
           // }

            if ("${env.BRANCH_NAME}" == 'master') {
               // utils.sendNotification(slackChannel: 'jenkinsjobs', sendSlackMessage: true, buildStatus: 'STARTED', customMessage: 'Building lgr docker image')
                def microservices = ['lgr-base', 'lgr-django', 'lgr-celery', 'lgr-gunicorn', 'lgr-static']
                microservices.each() {
                  sh label: "build image ${it}", script: "tar -czh -C containers/${it} . | docker build -t ${it} -"
                  utils.pushImageToRegistryTrunkBased(DTROrg: 'icann', DTRRepo: it, dockerImageName: it)
                }
            } else {
                echo "not master branch - skipping"
            }
        }
    }
    catch (e) {
        currentBuild.result = "FAILURE"
        throw e
    }
    finally {
        step([$class: 'Publisher'])
        // utils.sendNotification(slackChannel: 'jenkinsjobs', sendSlackMessage: true, buildStatus: currentBuild.result)
    }
}


def hasFileChanged(fileName){
    sh "git diff --name-only HEAD^ HEAD |egrep '^$fileName/'| wc -l > filechanged.txt"
        matches = readFile('filechanged.txt').trim()

        if (matches.toInteger() > 0){
            return true
        }
      return false
}

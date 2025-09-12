@Library('ICANN_LIB') _

utils = new icann.Utilities()

properties(
    [
        [
            $class: 'BuildDiscarderProperty',
            strategy: [
                $class: 'LogRotator',
                artifactDaysToKeepStr: '14',
                artifactNumToKeepStr: '10',
                daysToKeepStr: '14',
                numToKeepStr: '10'
            ]
        ],
        parameters([
            booleanParam(
                name: 'FORCE_HELM_CHART_REBUILD',
                defaultValue: false,
                description: 'Force the stage "Deploy LGR Helm Chart".'
            )
        ])
    ]
)

def registry = 'artifactory.icann.org/docker'
def pillar = 'icann'

pipeline {
    agent {
        label 'okd-jenkins-build-lax-docker'
    }

    stages {
        stage('Starting Build') {
            steps {
                script {
                    echo "Change Branch ${env.CHANGE_BRANCH}"
                    echo "Target Branch ${env.CHANGE_TARGET}"
                }
            }
        }

        stage('Initialize') {
            steps {
                checkout scm
            }
        }

        stage('Run Test Suite') {
            steps {
                script {
                    echo "Building image for tests"
                    sh label: "build image lgr-base", script: "tar -czh -C containers/lgr-base . | docker build -t lgr-base -"
                    sh label: "build image lgr-django", script: "tar -czh -C containers/lgr-django . | docker build -t lgr-django -"
                    sh label: "run test suite", script: """
                        docker run --rm lgr-django /bin/bash -c "
                        source /var/www/lgr/venv/bin/activate &&
                        pip install -i https://artifactory.icann.org/artifactory/api/pypi/pypi/simple parameterized &&
                        python manage.py test src --settings lgr_web.settings.test"
                    """
                }
            }
        }

        stage('Build and Push Images to Docker Registry') {
            when {
                branch 'master'
            }
            steps {
                script {
                    def images = ['lgr-base', 'lgr-django', 'lgr-celery', 'lgr-gunicorn', 'lgr-static']
                    images.each {
                        sh label: "build image ${it}", script: "tar -czh -C containers/${it} . | docker build -t ${it} -"
                        utils.pushImageToRegistrySingle(DTRUrl: registry, DTROrg: "${pillar}", DTRRepo: it, dockerImageName: it)
                    }
                }
            }
        }

        stage('Deploy LGR Helm Chart') {
            when {
                anyOf {
                    expression { return params.FORCE_HELM_CHART_REBUILD }
                    allOf {
                        branch 'master'
                        expression { return utils.hasFolderChanged("helm") }
                    }
                }
            }
            steps {
                script {
                    helmChart = "helm/lgr"
                    tag_details = utils.tagHelmChart(
                        directory: helmChart,
                        registry: registry
                    )
                    utils.pushHelmChart(directory: helmChart, artifactoryPath: "icann")
                }
            }
        }

        stage('Trigger Spinnaker Pipeline Webhooks') {
            when {
                branch 'master'
            }
            steps {
                script {
                    imageTag = utils.generateDockerTag();
                    artifacts = [
                        [
                            "type"     : "docker/image",
                            "name"     : "${registry}/${pillar}/lgr-base",
                            "version"  : imageTag,
                            "reference": "${registry}/${pillar}/lgr-base:${imageTag}"
                        ],
                        [
                            "type"     : "docker/image",
                            "name"     : "${registry}/${pillar}/lgr-django",
                            "version"  : imageTag,
                            "reference": "${registry}/${pillar}/lgr-django:${imageTag}"
                        ],
                        [
                            "type"     : "docker/image",
                            "name"     : "${registry}/${pillar}/lgr-celery",
                            "version"  : imageTag,
                            "reference": "${registry}/${pillar}/lgr-celery:${imageTag}"
                        ],
                        [
                            "type"     : "docker/image",
                            "name"     : "${registry}/${pillar}/lgr-gunicorn",
                            "version"  : imageTag,
                            "reference": "${registry}/${pillar}/lgr-gunicorn:${imageTag}"
                        ],
                        [
                            "type"     : "docker/image",
                            "name"     : "${registry}/${pillar}/lgr-static",
                            "version"  : imageTag,
                            "reference": "${registry}/${pillar}/lgr-static:${imageTag}"
                        ],
                    ]
                    utils.spinnakerTrigger(webhook: 'lgr-qa', artifacts: artifacts)
                    jiraSendDeploymentInfo environmentId: 'qa', environmentName: 'qa', environmentType: 'testing'
                }
            }
            post {
                always {
                    jiraSendDeploymentInfo  environmentId: 'qa', environmentName: 'qa', environmentType: 'testing'
                    jiraSendDeploymentInfo environmentId: 'uat', environmentName: 'uat', environmentType: 'staging'
                }
            }
        }
    }

    post {
        success {
            script {
                jiraSendBuildInfo()
            }
        }
        failure {
            script {
                jiraSendBuildInfo()
            }
        }
        cleanup {
            cleanWs()
        }
    }
}

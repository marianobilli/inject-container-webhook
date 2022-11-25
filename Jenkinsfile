#!/usr/bin/env groovy
@Library("jenkins-libraries") _

if( "${env.BRANCH_NAME}" == "master" ) {
    dockerPipeline (name: "doplat/webhook-project")
}
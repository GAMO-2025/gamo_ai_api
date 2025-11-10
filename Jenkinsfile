pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/GAMO-2025/gamo_ai_api.git'
            }
        }

        stage('Deploy to AI Server') {
            steps {
                sshagent(['ai-server-ssh']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no pjhyun0225@<AI_SERVER_IP> '
                            cd /home/pjhyun0225/gamo_ai_api &&
                            git pull origin main &&
                            pm2 restart gamo-ai || pm2 start app.py --name gamo-ai
                        '
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ 배포 성공!'
        }
        failure {
            echo '❌ 배포 실패... 로그 확인 필요'
        }
    }
}

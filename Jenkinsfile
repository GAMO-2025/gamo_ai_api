pipeline {
    agent any

    environment {
        // 배포 관련 정보
        DEPLOY_USER = 'pjhyun0225'
        DEPLOY_HOST = '34.158.203.193'
        DEPLOY_PATH = '/home/pjhyun0225/gamo_ai_api'
        PYTHON_ENV = 'python3' 
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'GitHub main 브랜치 코드 체크아웃 중...'
                git branch: 'main', credentialsId: 'github-clone', url: 'https://github.com/GAMO-2025/gamo_ai_api.git'
            }
        }

        stage('Deploy to AI Server') {
            steps {
                echo '서버에 SSH 접속하여 배포 시작...'
                sshagent(['ai-server-ssh']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST "
                            echo '배포 경로로 이동 중: $DEPLOY_PATH'
                            cd $DEPLOY_PATH || exit 1

                            echo '최신 main 코드로 업데이트 중...'
                            git fetch origin main &&
                            git reset --hard origin/main

                            echo '기존 uvicorn 프로세스 종료 중...'
                            pkill -f 'uvicorn' || true

                            echo 'FastAPI 서버 재실행 중...'
                            nohup $PYTHON_ENV -m uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

                            echo '배포 완료!'
                        "
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'FastAPI 서비스가 정상적으로 재배포되었습니다'
        }
        failure {
            echo '배포 실패. Jenkins 콘솔 로그를 확인하세요.'
        }
    }
}
 
pipeline {
    agent any

    parameters {
        string(name: 'DEPLOY_USER', defaultValue: 'pjhyun0225', description: 'SSH 접속 사용자명')
        string(name: 'DEPLOY_HOST', defaultValue: '34.158.203.193', description: '배포 대상 서버 IP')
        string(name: 'DEPLOY_PATH', defaultValue: '/home/pjhyun0225/gamo_ai_api', description: '프로젝트 배포 경로')
        string(name: 'PYTHON_ENV', defaultValue: '/home/pjhyun0225/gamo_ai_api/venv/bin/python3', description: 'Python 실행 경로 (가상환경 포함)')
        string(name: 'SSH_CREDENTIAL_ID', defaultValue: 'ai-server-ssh', description: 'SSH 자격 증명 ID')
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
                echo "서버(${params.DEPLOY_HOST})에 SSH 접속하여 배포 시작..."
                sshagent(["${params.SSH_CREDENTIAL_ID}"]) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${params.DEPLOY_USER}@${params.DEPLOY_HOST} << 'EOF'
                            echo '배포 경로로 이동 중: ${params.DEPLOY_PATH}'
                            cd ${params.DEPLOY_PATH} || exit 1

                            echo '최신 main 코드로 업데이트 중...'
                            git fetch origin main &&
                            git reset --hard origin/main

                            echo '기존 uvicorn 프로세스 강제 종료 중...'
                            pkill -9 -f 'uvicorn' || true

                            echo '가상환경 활성화 및 패키지 설치 중...'
                            if [ -d "venv" ]; then
                                source venv/bin/activate
                            else
                                echo '가상환경이 없으므로 새로 생성합니다.'
                                python3 -m venv venv
                                source venv/bin/activate
                            fi

                            pip install --upgrade pip
                            if [ -f "requirements.txt" ]; then
                                pip install -r requirements.txt
                            else
                                echo 'requirements.txt 파일이 없습니다.'
                            fi

                            echo 'FastAPI 서버 재실행 중...'
                            nohup ${params.PYTHON_ENV} -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

                            echo '배포 완료.'
                            exit 0
EOF
                    """
                }
            }
        }
    }

    post {
        success {
            echo 'FastAPI 서비스가 정상적으로 재배포되었습니다.'
        }
        failure {
            echo '배포 실패. Jenkins 콘솔 로그를 확인하세요.'
        }
    }
}

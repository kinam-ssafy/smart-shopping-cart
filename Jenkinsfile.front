pipeline {
    agent any
    
    environment {
        // Docker 이미지 이름
        DOCKER_IMAGE = 'smart-cart-frontend'
        // 컨테이너 이름
        CONTAINER_NAME = 'smart-cart-frontend'
        // 포트 설정 (EC2 포트 제한: 8000-9000)
        HOST_PORT = '8002'
        CONTAINER_PORT = '3000'
        // 백엔드 API URL (EC2 퍼블릭 IP로 변경 필요)
        API_URL = 'https://i14a401.p.ssafy.io'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 코드 체크아웃...'
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo '🐳 Docker 이미지 빌드 중...'
                dir('smart_shopping_cart_front') {
                    sh '''
                        docker build \
                            --build-arg NEXT_PUBLIC_API_URL=${API_URL} \
                            -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                        docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }
        
        stage('Stop Previous Container') {
            steps {
                echo '🛑 이전 컨테이너 정지...'
                sh '''
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo '🚀 새 컨테이너 배포...'
                sh '''
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        -p ${HOST_PORT}:${CONTAINER_PORT} \
                        --restart unless-stopped \
                        ${DOCKER_IMAGE}:latest
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                echo '💚 헬스 체크...'
                sh '''
                    sleep 10
                    curl -f http://172.17.0.1:${HOST_PORT} || exit 1
                '''
            }
        }
        
        stage('Cleanup') {
            steps {
                echo '🧹 오래된 이미지 정리...'
                sh '''
                    docker image prune -f
                '''
            }
        }
    }
    
    post {
        success {
            echo '✅ 배포 성공!'
        }
        failure {
            echo '❌ 배포 실패!'
        }
    }
}

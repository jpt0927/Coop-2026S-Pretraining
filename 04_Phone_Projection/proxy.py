import socket
import threading
import random

# 설정
LOCAL_PORT = 5277   # DHU가 접속할 포트 (가짜 서버)
REMOTE_PORT = 5278  # 실제 폰(ADB)으로 연결된 포트

def hexdump(data):
    return " ".join("{:02x}".format(c) for c in data[:16]) + "..."

# 데이터 변조 함수
def fuzz_data(data, direction):
    # 1% 확률로 데이터 길이를 뻥튀기하거나 이상한 값을 넣음
    if random.random() < 0.01:
        if len(data) > 4:
            print(f"[🔥 FUZZING!] {direction} 패킷 변조 시도!")
            
            # 특정 바이트를 랜덤하게 바꿈
            mutable_data = bytearray(data)
            idx = random.randint(0, len(mutable_data) - 1)
            mutable_data[idx] = random.randint(0, 255)
            return bytes(mutable_data)

    return data

def forward(source, destination, direction):
    while True:
        try:
            data = source.recv(4096)
            if len(data) == 0: break
            
            fuzzed_data = fuzz_data(data, direction)

            print(f"[{direction}] {len(data)} bytes: {hexdump(data)}")
            destination.send(fuzzed_data)
        except:
            break
    source.close()
    destination.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', LOCAL_PORT))
    server.listen(1)
    print(f"[*] 공격 대기 중... DHU를 실행하세요 (Port: {LOCAL_PORT})")

    while True:
        client_socket, addr = server.accept()
        print(f"[*] DHU 접속됨! 폰(ADB Port {REMOTE_PORT})과 연결 시도...")

        try:
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect(('127.0.0.1', REMOTE_PORT))

            # 양방향 중계 시작
            t1 = threading.Thread(target=forward, args=(client_socket, remote_socket, "DHU->Phone"))
            t2 = threading.Thread(target=forward, args=(remote_socket, client_socket, "Phone->DHU"))
            t1.start()
            t2.start()
        except Exception as e:
            print(f"[!] 폰 연결 실패: {e}")
            client_socket.close()

if __name__ == '__main__':
    start_server()

#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <stdio.h>  
#include <stdlib.h>  
#include <string.h>  
#include <WinSock2.h>
#include <math.h>
#include <time.h>
#include <chrono>
#include <vector>

#include "cJSON.h"
#define BUF_SIZE    1024
#define MSG_TYPE_NOTIFY_TO_FRONTEND (0)
#define MSG_TYPE_DEVICE_CONTROL     (1)

#pragma comment(lib,"ws2_32.lib")
void error_handling(const char* message);
char hello_str[] = "hello";
char message_buff[1024] = { 0 };

std::vector<long long> g_time_vec;

//hard-coding 
//TO DO
int g_fan_3  = 0;
int g_fan_23 = 0;
int g_water_tank_5 = 1;
int g_water_tank_25 = 1;


// 获取当前时间的微秒数  
long long getCurrentMilliseconds() {

    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto microseconds = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return microseconds;
}


static int get_device_data(char* buff, int len){
    char temp[BUF_SIZE] = { 0 };
    cJSON* root = cJSON_CreateObject();
    int num = 0;
    switch (rand() % 5) {
    case 0://gas
        if (rand() % 2 == 0) {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0001");
        }
        else {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0021");
        }
        snprintf(temp, BUF_SIZE, "%.3f", 0.04 + rand() % 10 * 0.001);
        cJSON_AddStringToObject(root, "CO", temp);
        memset(temp, 0, BUF_SIZE);

        snprintf(temp, BUF_SIZE, "%.3f", 0.07 + rand() % 10 * 0.001);
        cJSON_AddStringToObject(root, "HCL", temp);
        memset(temp, 0, BUF_SIZE);

        snprintf(temp, BUF_SIZE, "%.3f", 0.01 + rand() % 15 * 0.001);
        cJSON_AddStringToObject(root, "SO2", temp);
        memset(temp, 0, BUF_SIZE);

        break;
    case 1://temperature
        if (rand() % 2 == 0) {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0002");
        }
        else {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0022");
        }

        snprintf(temp, BUF_SIZE, "%.3f", 49.1 + rand() % 50 * 0.01);
        cJSON_AddStringToObject(root, "humidity", temp);
        memset(temp, 0, BUF_SIZE);

        snprintf(temp, BUF_SIZE, "%.3f", 24.6 + rand() % 50 * 0.01);
        cJSON_AddStringToObject(root, "temperature", temp);
        memset(temp, 0, BUF_SIZE);

        break;
    case 2://air-flow-meter
        num = (rand() % 2) == 0 ? 3 : 23;
        if (num == 3) {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0003");
            snprintf(temp, BUF_SIZE, "%.2f",pow(10,g_fan_3) - 1 + rand() % 15 *  0.05);
            cJSON_AddStringToObject(root, "flow-rate", temp);
            memset(temp, 0, BUF_SIZE);
        }
        else {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0023");
            snprintf(temp, BUF_SIZE, "%.2f", pow(10, g_fan_23) - 1  + rand() % 15 * 0.05);
            cJSON_AddStringToObject(root, "flow-rate", temp);
            memset(temp, 0, BUF_SIZE);
        }
 

        break;
    case 3://water-meter
        if (rand() % 2 == 0) {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0004");
        }
        else {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0024");
        }

        snprintf(temp, BUF_SIZE, "%.3f", 94.1 + rand() % 150 * 0.01);
        cJSON_AddStringToObject(root, "flow-rate", temp);
        memset(temp, 0, BUF_SIZE);

        snprintf(temp, BUF_SIZE, "%.3f", 3000 + rand() % 1500 * 0.1);
        cJSON_AddStringToObject(root, "water-pressure", temp);
        memset(temp, 0, BUF_SIZE);
        break;
    case 4://water-tank
        
        num = (rand() % 2) == 0 ? 5 : 25;
        if (num == 5) {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0005");
            snprintf(temp, BUF_SIZE, "%.3f", g_water_tank_5 * 0.6 + (rand() % 10) * 0.01);
            cJSON_AddStringToObject(root, "water-amount", temp);
            memset(temp, 0, BUF_SIZE);
        }
        else {
            cJSON_AddStringToObject(root, "device-sn", "aaaa0025");
            snprintf(temp, BUF_SIZE, "%.3f", g_water_tank_25 * 0.6 + (rand() % 10) * 0.01);
            cJSON_AddStringToObject(root, "water-amount", temp);
            memset(temp, 0, BUF_SIZE);
        }
        

        break;
    }
    
    char* jsonString = cJSON_PrintUnformatted(root);
    strcpy_s(buff, BUF_SIZE, jsonString);
    cJSON_Delete(root);
    free(jsonString);
    return 0;
}

int packing_data(char* buff, int len) {
    //BF01|notify-to-frontend|0|1695691644857589${"device-sn":"aaaa0002","humidity":51.85,"temperature":25.56}
    
    char temp[BUF_SIZE] = { 0 };
    snprintf(temp, len, "BF01|notify-to-frontend|0|%lld$%s%c",  getCurrentMilliseconds(), buff,4);
    strncpy_s(buff,BUF_SIZE, temp, strlen(temp));
    return 0;
}

int process_receive_data(char* input_data, int* msg_type, long long* msg_id,int* resend,char* json_data,int json_data_len ) {
    //BF01 | device_control | 0 | 1695691644857589${"device-sn" :  "bbbb0003","operation" : "set-wind-pump-speed","fan-speed" : 3}
    //替换掉buff中的\t \n \s
    int len = 0 , 
        str_len = 0, 
        dollar_pos = 0, 
        last_pip_pos = 0, 
        second_to_last_pip_pos = 0, 
        copy_len =0;

    len = (int)strlen(input_data);
    for (int i = 0; i < len; i++) {
        if (input_data[i] == '\t' || input_data[i] == '\n' || input_data[i] == 0x20) {
            memcpy(input_data + i, input_data + i + 1, len - i );
            input_data[len - 1] = '\0';
            len--;
            i--;
        }
    }

    str_len = (int)strlen(input_data);
    dollar_pos = int(strchr(input_data, '$') - input_data);
    
    if (strstr(input_data, "device_control")) {
        *msg_type = MSG_TYPE_DEVICE_CONTROL;
    }
    else if (strstr(input_data, "notify-to-frontend")) {
        *msg_type = MSG_TYPE_NOTIFY_TO_FRONTEND;
    }
    else {
        return -1;
    }
    last_pip_pos = int(strrchr(input_data, '|') - input_data);
    second_to_last_pip_pos = int(strrchr(input_data + last_pip_pos , '|') - input_data);
    for (int i = last_pip_pos - 1; i > 0; i--) {
        if (input_data[i] == '|') {
            second_to_last_pip_pos = i;
            break;
        }
    }
    
    if (last_pip_pos > dollar_pos) {
        return -1;
    }
    if (sscanf_s(input_data + last_pip_pos, "|%llu$", msg_id) <= 0) {
        return -1;
    }
    if (sscanf_s(input_data + second_to_last_pip_pos, "|%d|", resend) <= 0) {
        return -1;
    }

    copy_len = str_len - 1 - dollar_pos - 1;
    // remove EOF
    if (memcpy_s(json_data, json_data_len, input_data + dollar_pos + 1, copy_len) != 0) {
        return -1;
    }
    json_data[copy_len] = '\0';
    return 0;
}

int change_fan_speed(char* json_data) {
    //{"device-sn" :  "bbbb0003","operation" : "set-wind-pump-speed","fan-speed" : 3}

    cJSON* root = cJSON_Parse(json_data);
    cJSON* operation = NULL;
    cJSON* fan_speed = NULL;
    cJSON* device_sn = NULL;
    int speed = 0;
    int ret = 0;
    if (root == NULL) {
        error_handling("get json object fail");
        ret = -1;
        goto end;
    }
    operation = cJSON_GetObjectItemCaseSensitive(root, "operation");
    fan_speed = cJSON_GetObjectItemCaseSensitive(root, "fan-speed");
    device_sn = cJSON_GetObjectItemCaseSensitive(root, "device-sn");
    if (operation == NULL || fan_speed == NULL || operation == NULL) {
        error_handling("node is empty");
        ret = -1;
        goto end;
    }

    if (strcmp("set-wind-pump-speed", operation->valuestring) != 0 || !cJSON_IsNumber(fan_speed)) {
        ret = -1;
        goto end;
    }

    //hard-coding 
    //TO DO
    if (strcmp("bbbb0003", device_sn->valuestring) == 0)
    {
        speed = int(fan_speed->valuedouble);
        g_fan_3 = speed;
    }
    else if (strcmp("bbbb0023", device_sn->valuestring) == 0) {
        speed = int(fan_speed->valuedouble);
        g_fan_23 = speed;
    }

end:
    cJSON_free(root);
    return ret;
}

int main(int argc, char* argv[]) {
    SOCKET serv_sock, clnt_sock;
    char buf[BUF_SIZE];
    char str_buf[BUF_SIZE];
    char json_data[BUF_SIZE] = { 0 };
    SOCKADDR_IN serv_adr = { 0 }, clnt_adr = { 0 };
    int adr_sz, ret;
    WSADATA wsa_data;
    fd_set reads = { 0 }, cpy_reads = { 0 };
    TIMEVAL timeout = { 0 };
    int  str_len, fd_num;
    srand((unsigned)time(NULL));

  
    if (argc != 2) {
        printf("Usage : %s <port>\n", argv[0]);
        exit(1);
    }

    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != NOERROR) {
        error_handling("WSAStartup() error\n");
    }

    serv_sock = socket(PF_INET, SOCK_STREAM, 0);
    if (serv_sock == INVALID_SOCKET) {
        error_handling("socket error");
    }

    memset(&serv_adr, 0, sizeof(serv_adr));
    serv_adr.sin_family = AF_INET;
    serv_adr.sin_addr.s_addr = htonl(INADDR_ANY);
    serv_adr.sin_port = htons(atoi(argv[1]));

    if (bind(serv_sock, (SOCKADDR*)&serv_adr, sizeof(serv_adr)) == SOCKET_ERROR) {
        error_handling("bind() error");
    }

    if (listen(serv_sock, 5) == SOCKET_ERROR) {
        error_handling("listen() error");
    }

    FD_ZERO(&reads);
    FD_SET(serv_sock, &reads);
    



    while (1) {
        cpy_reads = reads;
        timeout.tv_sec = 0;
        timeout.tv_usec = 0;
        Sleep(100);
        if ((fd_num = select(0, &cpy_reads, 0, 0, &timeout)) == SOCKET_ERROR)
            break;
        if (fd_num == 0) {
            for (UINT i = 0; i < reads.fd_count; i++) {
                if (reads.fd_array[i] == serv_sock) {
                    continue;
                }
                memset(str_buf, 0, BUF_SIZE);
                get_device_data(str_buf, BUF_SIZE);
                packing_data(str_buf, BUF_SIZE);
                str_len = send(reads.fd_array[i], str_buf, (int)strlen(str_buf), 0);
                if (str_len < 0) {
                    memset(str_buf, 0, BUF_SIZE);
                    snprintf(str_buf, sizeof(str_buf), "send error %d\n", WSAGetLastError());
                    error_handling(str_buf);
                }
            }
            continue;
        }

        for (UINT i = 0; i < reads.fd_count; i++) {
            if (FD_ISSET(reads.fd_array[i], &cpy_reads)) {
                if (reads.fd_array[i] == serv_sock) {	//connection request
                    adr_sz = sizeof(clnt_adr);
                    clnt_sock = accept(serv_sock, (struct sockaddr*)&clnt_adr, &adr_sz);
                    FD_SET(clnt_sock, &reads);

                    printf("connected client : %lld \n", clnt_sock);
                }
                else {	//read message
                    memset(buf, 0, BUF_SIZE);
                    str_len = recv(reads.fd_array[i], buf, BUF_SIZE - 1,0);
                    
                    if (str_len < 0) {
                        printf("recv str_len %d \n", str_len);
                        FD_CLR(reads.fd_array[i], &reads);
                        closesocket(cpy_reads.fd_array[i]);
                    }

                    if (str_len == 0) {	//close
                        FD_CLR(reads.fd_array[i], &reads);
                        closesocket(cpy_reads.fd_array[i]);
                        printf("closed client %lld \n", reads.fd_array[i]);
                    }
                    if (str_len > 0){
                        //如果接收到控制消息
                        printf("%s\n", buf);
                        int msg_type = 0;
                        long long msg_id = 0;
                        int resend = 0;
                        
                        ret = process_receive_data(buf, &msg_type, &msg_id, &resend, json_data, BUF_SIZE);
                        if (ret < 0 && msg_type != MSG_TYPE_DEVICE_CONTROL) {
                            continue;
                        }
                        //处理消息//只写个风机
                        change_fan_speed(json_data);

                        //检查g_time_vec是否处理过这个消息（不实现）
                        //处理完后保存到g_time_vec中（不实现）
                        //检查到10分钟以上的消息，去掉该消息（不实现）
                    }
                }
            }
        }
    }
    closesocket(serv_sock);

    return 0;
}

void error_handling(const char* message) {

    fputs(message, stderr);
    exit(1);
}



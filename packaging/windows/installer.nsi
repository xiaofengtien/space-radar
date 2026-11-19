Unicode true

; ============================================================================
; SpaceRadar · 空间雷达 - NSIS 现代化安装引导程序脚本 (MUI2)
; 支持 x64 Windows 10 / 11 原生安装、桌面与开始菜单快捷方式、完整卸载与注册表登记
; ============================================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; -----------------------------
; 基础产品元信息定义
; -----------------------------
!define PRODUCT_NAME "SpaceRadar"
!define PRODUCT_NAME_CN "空间雷达"
!define PRODUCT_DISPLAY_NAME "SpaceRadar · 空间雷达"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "SpaceRadar Team"
!define PRODUCT_WEB_SITE "https://github.com/xiaofengtien/space-radar"
!define PRODUCT_DIR_REGKEY "Software\SpaceRadar"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\SpaceRadar"
!define PRODUCT_UNINST_ROOT_KEY HKCU

; -----------------------------
; 编译器输出与压缩设置
; -----------------------------
Name "${PRODUCT_DISPLAY_NAME} v${PRODUCT_VERSION}"
OutFile "..\..\dist\SpaceRadar-Setup-v${PRODUCT_VERSION}-win64.exe"
InstallDir "$LOCALAPPDATA\Programs\SpaceRadar"
InstallDirRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_DIR_REGKEY}" ""

; 采用 LZMA 极限高压缩比，大幅降低安装包体积
SetCompressor /SOLID lzma
RequestExecutionLevel user

; -----------------------------
; 界面与图标资源
; -----------------------------
!define MUI_ICON "..\..\assets\app_icon.ico"
!define MUI_UNICON "..\..\assets\app_icon.ico"
!define MUI_ABORTWARNING

; -----------------------------
; 安装向导页面定义 (Modern UI 2)
; -----------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; 安装完成页 (支持直接勾选运行程序)
!define MUI_FINISHPAGE_RUN "$INSTDIR\SpaceRadar.exe"
!define MUI_FINISHPAGE_RUN_TEXT "立即运行 ${PRODUCT_DISPLAY_NAME}"
!insertmacro MUI_PAGE_FINISH

; -----------------------------
; 卸载向导页面定义
; -----------------------------
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; -----------------------------
; 多语言支持配置 (规范：必须置于所有 MUI_PAGE 之后！)
; -----------------------------
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; -----------------------------
; 主安装逻辑区段
; -----------------------------
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite on

    ; 释放 PyInstaller 打包生成的所有文件与依赖
    File /r "..\..\dist\SpaceRadar\*.*"

    ; 写入安装路径到注册表
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR"

    ; 创建开始菜单程序快捷方式
    CreateDirectory "$SMPROGRAMS\${PRODUCT_DISPLAY_NAME}"
    CreateShortcut "$SMPROGRAMS\${PRODUCT_DISPLAY_NAME}\${PRODUCT_DISPLAY_NAME}.lnk" "$INSTDIR\SpaceRadar.exe" "" "$INSTDIR\SpaceRadar.exe" 0
    CreateShortcut "$SMPROGRAMS\${PRODUCT_DISPLAY_NAME}\卸载 ${PRODUCT_DISPLAY_NAME}.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

    ; 创建桌面快捷方式
    CreateShortcut "$DESKTOP\${PRODUCT_DISPLAY_NAME}.lnk" "$INSTDIR\SpaceRadar.exe" "" "$INSTDIR\SpaceRadar.exe" 0

    ; 写入 Windows 标准控制面板「添加或删除程序」卸载注册表条目
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_DISPLAY_NAME}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\SpaceRadar.exe,0"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "NoModify" 1
    WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "NoRepair" 1

    ; 计算估算磁盘占用大小
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"

    ; 生成卸载执行程序
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; -----------------------------
; 卸载清理逻辑区段
; -----------------------------
Section Uninstall
    ; 删除快捷方式
    Delete "$DESKTOP\${PRODUCT_DISPLAY_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_DISPLAY_NAME}\${PRODUCT_DISPLAY_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_DISPLAY_NAME}\卸载 ${PRODUCT_DISPLAY_NAME}.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_DISPLAY_NAME}"

    ; 递归删除安装目录下所有文件与文件夹
    RMDir /r "$INSTDIR"

    ; 清除注册表项
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_DIR_REGKEY}"

    SetAutoClose true
SectionEnd
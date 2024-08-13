# Kootomation Installer for NSIS

;-------------------------------
!define MAJORMINORVER "0.1"
!define BUILDVER "3"
;--------------------------------
# Name of the installer
Name "Kootomation Version ${MAJORMINORVER}"
# Installer exe name
OutFile "Kootomation_${MAJORMINORVER}.${BUILDVER}_installer.exe"
RequestExecutionLevel user

;--------------------------------
; Version Information

VIProductVersion "${MAJORMINORVER}.${BUILDVER}.0"
VIAddVersionKey "ProductName" "Kootomation V${MAJORMINORVER}"
VIAddVersionKey "Comments" "Data Processing Automation Software"
VIAddVersionKey "CompanyName" "Firefly Aerospace"
VIAddVersionKey "FileDescription" "Data Processing Software Installer"
VIAddVersionKey "ProductVersion" "${MAJORMINORVER}.${BUILDVER}"
VIAddVersionKey "FileVersion" "${MAJORMINORVER}.${BUILDVER}"

;--------------------------------

# Location to install
InstallDir "C:\Program Files FF\kootomation\release"

# Include modern UI
!include "MUI2.nsh"
!include "LogicLib.nsh"

# Define your custom welcome image
!define MUI_WELCOMEFINISHPAGE_BITMAP "C:\avi_tools\kootomation\src\opening_installer_image.bmp"

# Configure the GUI page
!define MUI_ICON "C:\avi_tools\kootomation\src\final_ico.ico"
!define MUI_WELCOMEPAGE_TEXT "Click 'Install' to install Kootomation in: C:\Program Files FF\kootomation\release. If this directory exists, it will be removed and overwritten."
!define MUI_INSTFILESPAGE_ABORTHEADER_TEXT "Install Failed"
!define MUI_FINISHPAGE_TEXT "Kootomation has been installed at: C:\Program Files FF\kootomation\release."

# Pages for installation
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

# Include language macro (this must be after the pages)
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${If} ${Silent}
    SetSilent silent
  ${EndIf}
FunctionEnd

# Default section
Section

  # Set output location
  SetOverWrite on
  SetOutPath $INSTDIR

  # If it exists, delete the old directory
  IfFileExists "$INSTDIR" 0 +7  # True: jump 0 lines | False: jump 7 lines
    RMDir /r $INSTDIR  # The following code ensures it's done deleting before moving on
    StrCpy $R1 0
    ${While} $R1 < 1
      IfFileExists $INSTDIR +1 0 # True: jump 1 lines | False: jump 0 lines
        IntOp $R1 $R1 + 1
    ${EndWhile}

  # Copy Kootomation executable and all associated files
  File /r "C:\avi_tools\kootomation\src\dist\Kootomation\*.*"

  # Create shortcut
  CreateShortcut "$SMPROGRAMS\Kootomation_v${MAJORMINORVER}.lnk" "$INSTDIR\Kootomation.exe" "" "$INSTDIR\final_ico.ico"

SectionEnd
Write-Host "Petal Installer v0.0"
Write-Host "Checking if petal directory already exists..."

If (-Not (Test-Path "$env:temp\petal")) {
	$folder = New-Item -ItemType directory -Path "$env:temp\petal"
	}
Else {
	$folder = "$env:temp\petal"
	}
	
cd $folder
Write-Host "Ready to begin, press enter"
Read-Host 
If (-Not (Test-Path "python3.5installer.exe")) {
	Write-Host "Installing python3.5..."
	Write-Host "NOTE: Please check the option 'Add python to path' during the installation to prevent headaches"
	wget "https://www.python.org/ftp/python/3.5.0/python-3.5.0-amd64.exe" -OutFile python3.5installer.exe
	Start-Process -FilePath "python3.5installer.exe"
	Write-Host "Assuming you installed python correctly, press enter. Otherwise press CTRL+C"
	
	Read-Host
	$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User") 
	
}
Else {
Write-Host "Python detected already...Moving on!"
}

If (-Not (Test-Path "gitinstaller.exe")) {
	$title = "Install Git"
	$message = "Do you want to install Git.  It is reccomended in order for update.bat to work (requires 64-bit windows)"
	
	$yes = New-Object System.Management.Automation.Host.ChoiceDescription "&Install Git", `
		"Install git"

	$no = New-Object System.Management.Automation.Host.ChoiceDescription "&Skip", `
		"Dont install git"

	$options = [System.Management.Automation.Host.ChoiceDescription[]]($yes, $no)

	$result = $host.ui.PromptForChoice($title, $message, $options, 0) 

	switch ($result)
		{
			0 {
			wget "https://github.com/git-for-windows/git/releases/download/v2.11.0.windows.3/Git-2.11.0.3-64-bit.exe" -OutFile gitinstaller.exe 
			Start-Process -FilePath "gitinstaller.exe" 
			}
			1 {
			Write-Host "Skipping git install, Installer will download a static copy of petal"
			}
		}
	Write-Host "If git installed correctly, press enter. Otherwise press CTRL+C"
	Read-Host
	$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User") 
}
Else {
Write-Host "Git detected already...Moving on!"
}
If (-Not (Test-Path "get-pip.py")) {
	Write-Host "Downloading pip (This is a python package manager to install the extra stuff that petal needs to run. Get ready for a lot of lines!"
	wget "https://bootstrap.pypa.io/get-pip.py" -OutFile git-pip.py
	Write-Host "Download complete...Updating pip to newest version"
	python git-pip.py
	
	}
Else {
	Write-Host "Pip already installed. Updating pip"
}
pip install --upgrade pip 

pip install -U discord.py colorama requests cleverbot praw ruamel.yaml python-magic pytumblr python-twitter facebook-sdk 
Write-Host "Package installations/upgrades complete. Downloading petal. It will appear in your user directory " 
cd $home
Do {
	Write-Host "Please pick a folder name: "
	$x = Read-Host 
	} While (Test-Path "$home\$x")
$gitdir = "$home\$x"
New-Item -ItemType directory -Path $gitdir  	
cd $gitdir

$title = "Git mode"
$message = "Would you like to use git to install petal? "

$yes = New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", `
	"Use git"

$no = New-Object System.Management.Automation.Host.ChoiceDescription "&No", `
	"Dont use git"

$options = [System.Management.Automation.Host.ChoiceDescription[]]($yes, $no)

$result = $host.ui.PromptForChoice($title, $message, $options, 0) 

switch ($result)
	{
		0 {
		git clone https://github.com/hdmifish/petal.git "$gitdir/petal"
		}
		1 {
		Write-Host "Alright, static download it is! "
		wget "https://github.com/hdmifish/petal/archive/master.zip" -OutFile petal.zip
		Expand-Archive -LiteralPath petal.zip -DestinationPath .
		rm petal.zip 
		}
	}


ii ./petal-master

Write-Host "All done!"
Write-Host "If you are new to bots, or just wanna use a more dialog based configuration. Type ./petal_config.ps1"








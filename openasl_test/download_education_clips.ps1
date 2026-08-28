# ============================================================
# SignBridge - OpenASL Education Video Downloader
#
# What this script does:
#   1. Downloads the FULL YouTube source video
#   2. Repairs/converts it using FFmpeg
#   3. Cuts only the OpenASL sentence
#   4. Saves a clean MP4
#   5. Deletes large temporary files
#   6. Continues even if one video fails
#
# Requirements already prepared:
#   - yt-dlp inside .venv_fi
#   - Node.js
#   - FFmpeg
#   - cookies.txt
# ============================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================"
Write-Host " SIGNBRIDGE - EDUCATION VIDEO DOWNLOADER"
Write-Host "============================================================"
Write-Host ""

# ============================================================
# 1. Find FFmpeg
# ============================================================

$ffmpeg = "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ffmpeg.exe"

if (-not (Test-Path $ffmpeg)) {

    Write-Host "Searching for FFmpeg..."

    $foundFFmpeg = Get-ChildItem `
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" `
        -Filter "ffmpeg.exe" `
        -Recurse `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName

    if ($foundFFmpeg) {
        $ffmpeg = $foundFFmpeg
    }
}

if (-not (Test-Path $ffmpeg)) {

    Write-Host ""
    Write-Host "[ERROR] FFmpeg was not found."
    Write-Host "FFmpeg must be installed before running this script."
    Write-Host ""

    exit 1
}

Write-Host "[OK] FFmpeg:"
Write-Host $ffmpeg
Write-Host ""

# ============================================================
# 2. Check cookies.txt
# ============================================================

$cookiesFile = Join-Path $PSScriptRoot "cookies.txt"

if (-not (Test-Path $cookiesFile)) {

    Write-Host ""
    Write-Host "[ERROR] cookies.txt was not found."
    Write-Host ""
    Write-Host "Expected location:"
    Write-Host $cookiesFile
    Write-Host ""

    exit 1
}

Write-Host "[OK] cookies.txt found."
Write-Host ""

# ============================================================
# 3. Create folders
# ============================================================

$outputFolder = Join-Path $PSScriptRoot "education_clips"
$tempFolder   = Join-Path $PSScriptRoot "temp_sources"

New-Item `
    -ItemType Directory `
    -Path $outputFolder `
    -Force | Out-Null

New-Item `
    -ItemType Directory `
    -Path $tempFolder `
    -Force | Out-Null

Write-Host "[OK] Output folder:"
Write-Host $outputFolder
Write-Host ""

# ============================================================
# 4. Sentence dataset
#
# We intentionally give every sentence extra time before/after
# the OpenASL timestamp so that the sign is not cut too tightly.
# ============================================================

$clips = @(

    # --------------------------------------------------------
    # HELLO
    # OpenASL:
    # 00:00:06.000 -> 00:00:06.589
    # --------------------------------------------------------
    @{
        Name     = "hello"
        Sentence = "Hello!"
        VideoId  = "Mci9oyb5V2E"

        Start    = "00:00:05.200"
        Duration = "00:00:02.400"
    },

    # --------------------------------------------------------
    # THANK YOU
    #
    # Current version.
    # We can replace this source later with a better signer.
    #
    # OpenASL:
    # 00:03:09.010 -> 00:03:10.056
    # --------------------------------------------------------
    @{
        Name     = "thank_you"
        Sentence = "Thank you."
        VideoId  = "Swrk-C5k6bw"

        Start    = "00:03:08.200"
        Duration = "00:00:02.800"
    },

    # --------------------------------------------------------
    # HOW ARE YOU
    # OpenASL:
    # 00:12:03.899 -> 00:12:04.683
    # --------------------------------------------------------
    @{
        Name     = "how_are_you"
        Sentence = "How are you?"
        VideoId  = "Id8XymKwr2M"

        Start    = "00:12:03.300"
        Duration = "00:00:02.200"
    },

    # --------------------------------------------------------
    # ARE YOU READY
    # OpenASL:
    # 00:08:33.998 -> 00:08:34.960
    # --------------------------------------------------------
    @{
        Name     = "are_you_ready"
        Sentence = "Are you ready?"
        VideoId  = "0ozA6CspdcQ"

        Start    = "00:08:32.800"
        Duration = "00:00:03.300"
    },

    # --------------------------------------------------------
    # I'M FINE
    # OpenASL:
    # 00:10:04.519 -> 00:10:05.479
    # --------------------------------------------------------
    @{
        Name     = "im_fine"
        Sentence = "I'm fine!"
        VideoId  = "yYYYXAAbH7A"

        Start    = "00:10:03.700"
        Duration = "00:00:02.700"
    },

    # --------------------------------------------------------
    # SEE YOU LATER
    # OpenASL:
    # 00:00:21.899 -> 00:00:23.059
    # --------------------------------------------------------
    @{
        Name     = "see_you_later"
        Sentence = "See you later."
        VideoId  = "8y54C5UiktI"

        Start    = "00:00:20.800"
        Duration = "00:00:03.400"
    },

    # --------------------------------------------------------
    # SEE YOU SOON
    # OpenASL:
    # 00:05:45.863 -> 00:05:47.000
    # --------------------------------------------------------
    @{
        Name     = "see_you_soon"
        Sentence = "See you soon!"
        VideoId  = "1lqXl-xn0e4"

        Start    = "00:05:44.800"
        Duration = "00:00:03.400"
    },

    # --------------------------------------------------------
    # GOOD MORNING
    #
    # OpenASL sentence:
    # "Hello, good morning."
    #
    # 00:00:59.292 -> 00:01:01.594
    # --------------------------------------------------------
    @{
        Name     = "good_morning"
        Sentence = "Hello, good morning."
        VideoId  = "T6YFwhrRwh0"

        Start    = "00:00:58.300"
        Duration = "00:00:04.300"
    },

    # --------------------------------------------------------
    # GOOD NIGHT
    # OpenASL:
    # 00:08:42.451 -> 00:08:43.278
    # --------------------------------------------------------
    @{
        Name     = "good_night"
        Sentence = "Good night!"
        VideoId  = "OyQKY-d09iI"

        Start    = "00:08:41.500"
        Duration = "00:00:02.900"
    },

    # --------------------------------------------------------
    # WHAT IS YOUR NAME
    # OpenASL:
    # 00:05:14.079 -> 00:05:15.399
    # --------------------------------------------------------
    @{
        Name     = "what_is_your_name"
        Sentence = "What is your name?"
        VideoId  = "LXNi7HTTzWU"

        Start    = "00:05:13.000"
        Duration = "00:00:03.600"
    },

    # --------------------------------------------------------
    # NICE TO MEET YOU
    # OpenASL:
    # 00:01:45.599 -> 00:01:47.799
    # --------------------------------------------------------
    @{
        Name     = "nice_to_meet_you"
        Sentence = "Nice to meet you!"
        VideoId  = "jFh4BZRJLRI"

        Start    = "00:01:44.500"
        Duration = "00:00:04.500"
    }
)

# ============================================================
# 5. Statistics
# ============================================================

$total      = $clips.Count
$current    = 0
$successful = 0
$failed     = 0
$skipped    = 0

$failedNames = @()

# ============================================================
# 6. Process every sentence
# ============================================================

foreach ($clip in $clips) {

    $current++

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "[$current / $total]"
    Write-Host ""
    Write-Host "Sentence : $($clip.Sentence)"
    Write-Host "File     : $($clip.Name).mp4"
    Write-Host "YouTube  : $($clip.VideoId)"
    Write-Host "============================================================"
    Write-Host ""

    $finalFile = Join-Path `
        $outputFolder `
        "$($clip.Name).mp4"

    # ========================================================
    # Skip if final clip already exists
    # ========================================================

    if (Test-Path $finalFile) {

        $existingSize = (Get-Item $finalFile).Length

        if ($existingSize -gt 10000) {

            Write-Host "[SKIP] Final video already exists:"
            Write-Host $finalFile
            Write-Host ""

            $skipped++

            continue
        }
        else {

            Write-Host "[WARNING] Existing file is too small."
            Write-Host "Deleting and creating it again..."

            Remove-Item $finalFile -Force
        }
    }

    # ========================================================
    # Remove previous temporary files for this sentence
    # ========================================================

    Get-ChildItem `
        $tempFolder `
        -File `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -like "$($clip.Name)_source*"
        } |
        Remove-Item -Force -ErrorAction SilentlyContinue

    # ========================================================
    # Download FULL source video
    #
    # IMPORTANT:
    # We do NOT use --download-sections because that produced
    # 403 errors on this computer.
    #
    # 720p maximum is enough for Education and reduces size.
    # ========================================================

    $sourceTemplate = Join-Path `
        $tempFolder `
        "$($clip.Name)_source.%(ext)s"

    Write-Host "[1/4] Downloading full source..."
    Write-Host ""

    python -m yt_dlp `
        --cookies "$cookiesFile" `
        --js-runtimes node `
        --remote-components ejs:github `
        --ffmpeg-location "$ffmpeg" `
        --no-playlist `
        -f "bv*[height<=720]+ba/b[height<=720]/b" `
        --merge-output-format mp4 `
        "https://www.youtube.com/watch?v=$($clip.VideoId)" `
        -o "$sourceTemplate"

    $downloadExitCode = $LASTEXITCODE

    if ($downloadExitCode -ne 0) {

        Write-Host ""
        Write-Host "[FAILED] Download failed:"
        Write-Host $clip.Name
        Write-Host ""
        Write-Host "The script will continue with the next sentence."
        Write-Host ""

        $failed++
        $failedNames += $clip.Name

        continue
    }

    # ========================================================
    # Find downloaded file
    # ========================================================

    $sourceFile = Get-ChildItem `
        $tempFolder `
        -File `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.BaseName -like "$($clip.Name)_source*"
        } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $sourceFile) {

        Write-Host ""
        Write-Host "[FAILED] Source file could not be found."
        Write-Host ""

        $failed++
        $failedNames += $clip.Name

        continue
    }

    Write-Host ""
    Write-Host "[OK] Download complete:"
    Write-Host $sourceFile.FullName
    Write-Host ""

    # ========================================================
    # Repair / convert source to a standard MP4
    # ========================================================

    $fixedFile = Join-Path `
        $tempFolder `
        "$($clip.Name)_fixed.mp4"

    if (Test-Path $fixedFile) {
        Remove-Item $fixedFile -Force
    }

    Write-Host "[2/4] Repairing / converting source..."
    Write-Host ""

    & $ffmpeg `
        -y `
        -i "$($sourceFile.FullName)" `
        -c:v libx264 `
        -preset ultrafast `
        -crf 20 `
        -pix_fmt yuv420p `
        -c:a aac `
        -b:a 128k `
        -movflags +faststart `
        "$fixedFile"

    $fixExitCode = $LASTEXITCODE

    if ($fixExitCode -ne 0 -or -not (Test-Path $fixedFile)) {

        Write-Host ""
        Write-Host "[FAILED] FFmpeg conversion failed:"
        Write-Host $clip.Name
        Write-Host ""

        $failed++
        $failedNames += $clip.Name

        # Keep original source in case we need to inspect it.
        continue
    }

    Write-Host ""
    Write-Host "[OK] Source converted."
    Write-Host ""

    # ========================================================
    # Cut sentence
    # ========================================================

    Write-Host "[3/4] Cutting sentence..."
    Write-Host ""
    Write-Host "Start    : $($clip.Start)"
    Write-Host "Duration : $($clip.Duration)"
    Write-Host ""

    & $ffmpeg `
        -y `
        -ss "$($clip.Start)" `
        -i "$fixedFile" `
        -t "$($clip.Duration)" `
        -c:v libx264 `
        -preset veryfast `
        -crf 20 `
        -pix_fmt yuv420p `
        -c:a aac `
        -b:a 128k `
        -movflags +faststart `
        "$finalFile"

    $cutExitCode = $LASTEXITCODE

    if ($cutExitCode -ne 0 -or -not (Test-Path $finalFile)) {

        Write-Host ""
        Write-Host "[FAILED] Cutting failed:"
        Write-Host $clip.Name
        Write-Host ""

        $failed++
        $failedNames += $clip.Name

        continue
    }

    # ========================================================
    # Validate final file
    # ========================================================

    $finalSize = (Get-Item $finalFile).Length

    if ($finalSize -lt 10000) {

        Write-Host ""
        Write-Host "[FAILED] Final video is unexpectedly small."
        Write-Host ""

        Remove-Item $finalFile -Force -ErrorAction SilentlyContinue

        $failed++
        $failedNames += $clip.Name

        continue
    }

    Write-Host ""
    Write-Host "[OK] Final clip created:"
    Write-Host $finalFile
    Write-Host ""

    # ========================================================
    # Delete large source files after success
    # ========================================================

    Write-Host "[4/4] Removing temporary large files..."

    if (Test-Path $sourceFile.FullName) {

        Remove-Item `
            "$($sourceFile.FullName)" `
            -Force `
            -ErrorAction SilentlyContinue
    }

    if (Test-Path $fixedFile) {

        Remove-Item `
            "$fixedFile" `
            -Force `
            -ErrorAction SilentlyContinue
    }

    Write-Host "[SUCCESS] $($clip.Sentence)"
    Write-Host ""

    $successful++
}

# ============================================================
# 7. Remove empty temporary directory if possible
# ============================================================

$tempRemaining = Get-ChildItem `
    $tempFolder `
    -File `
    -ErrorAction SilentlyContinue

if (-not $tempRemaining) {

    Remove-Item `
        $tempFolder `
        -Force `
        -ErrorAction SilentlyContinue
}

# ============================================================
# 8. Final report
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " FINISHED"
Write-Host "============================================================"
Write-Host ""

Write-Host "Total      : $total"
Write-Host "Successful : $successful"
Write-Host "Skipped    : $skipped"
Write-Host "Failed     : $failed"
Write-Host ""

if ($failedNames.Count -gt 0) {

    Write-Host "Failed clips:"
    Write-Host ""

    foreach ($name in $failedNames) {
        Write-Host " - $name"
    }

    Write-Host ""
}

Write-Host "Final videos:"
Write-Host ""

Get-ChildItem `
    "$outputFolder\*.mp4" `
    -ErrorAction SilentlyContinue |
    Sort-Object Name |
    Select-Object `
        Name,
        @{Name="SizeMB"; Expression={
            [math]::Round($_.Length / 1MB, 2)
        }} |
    Format-Table -AutoSize

Write-Host ""
Write-Host "Output folder:"
Write-Host $outputFolder
Write-Host ""
Write-Host "============================================================"
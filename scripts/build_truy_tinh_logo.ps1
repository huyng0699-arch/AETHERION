$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$mobileDir = Join-Path $repo 'apps\mobile\assets'
$desktopDir = Join-Path $repo 'apps\desktop\src\aetherion_desktop\assets'
$null = New-Item -ItemType Directory -Force -Path $desktopDir
$output = Join-Path $mobileDir 'truy-tinh-logo.png'
$size = 1024

Add-Type -AssemblyName System.Drawing
$bitmap = [System.Drawing.Bitmap]::new($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
$graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$graphics.Clear([System.Drawing.Color]::Transparent)

$disc = [System.Drawing.Rectangle]::new(20, 20, 984, 984)
$fill = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
    $disc,
    [System.Drawing.Color]::FromArgb(255, 24, 10, 83),
    [System.Drawing.Color]::FromArgb(255, 14, 23, 66),
    42.0
)
$graphics.FillEllipse($fill, $disc)

$rim = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(220, 104, 64, 255), 13)
$graphics.DrawArc($rim, 46, 46, 932, 932, 205, 116)
$graphics.DrawArc($rim, 46, 46, 932, 932, 18, 54)

# The orbit, satellite, and star form one mark; no NASA insignia or lettering.
$state = $graphics.Save()
$graphics.TranslateTransform(512, 512)
$graphics.RotateTransform(-26)
$orbit = [System.Drawing.Drawing2D.GraphicsPath]::new()
$orbit.AddEllipse([single]-444, [single]-267, [single]888, [single]534)
$orbitPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(245, 245, 252, 255), 15)
$graphics.DrawPath($orbitPen, $orbit)
$satellite = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 245, 252, 255))
$graphics.FillEllipse($satellite, 254, -288, 54, 54)
$graphics.Restore($state)

$points = @(
    [System.Drawing.PointF]::new(512, 126),
    [System.Drawing.PointF]::new(570, 447),
    [System.Drawing.PointF]::new(896, 512),
    [System.Drawing.PointF]::new(570, 577),
    [System.Drawing.PointF]::new(512, 898),
    [System.Drawing.PointF]::new(454, 577),
    [System.Drawing.PointF]::new(128, 512),
    [System.Drawing.PointF]::new(454, 447)
)
$glowPoints = foreach ($point in $points) {
    [System.Drawing.PointF]::new(512 + ($point.X - 512) * 1.045, 512 + ($point.Y - 512) * 1.045)
}
$glowPath = [System.Drawing.Drawing2D.GraphicsPath]::new()
$glowPath.AddPolygon([System.Drawing.PointF[]]$glowPoints)
$cyan = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 21, 221, 244))
$graphics.FillPath($cyan, $glowPath)
$starPath = [System.Drawing.Drawing2D.GraphicsPath]::new()
$starPath.AddPolygon([System.Drawing.PointF[]]$points)
$white = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 255, 255))
$graphics.FillPath($white, $starPath)

$bitmap.Save($output, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
$fill.Dispose(); $rim.Dispose(); $orbit.Dispose(); $orbitPen.Dispose()
$satellite.Dispose(); $cyan.Dispose(); $glowPath.Dispose(); $starPath.Dispose(); $white.Dispose()
Copy-Item -LiteralPath $output -Destination (Join-Path $desktopDir 'truy-tinh-logo.png') -Force
Write-Output "Built Truy Tinh logo: $output"

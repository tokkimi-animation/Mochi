param(
  [Parameter(Mandatory=$true)][string]$OutDir
)

Add-Type -AssemblyName System.Speech
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$lines = @(
  @{ File="line_01_mochi.wav"; Rate=-1; Text="잠깐만. 저 별빛이 문 사이에 끼었어." },
  @{ File="line_02_zumu.wav"; Rate=2; Text="가자 가자! 내가 빨리 빼낼게!" },
  @{ File="line_03_mochi.wav"; Rate=-1; Text="내가 도와주려던 건데... 왜 더 무서워하지?" },
  @{ File="line_04_mochi.wav"; Rate=-2; Text="잡는 게 아니라, 기다려 줘야 했어." },
  @{ File="line_05_zumu.wav"; Rate=1; Text="정답보다 중요한 걸 찾았네." },
  @{ File="line_06_mochi.wav"; Rate=-1; Text="다음엔 더 늦게, 더 잘 볼래." },
  @{ File="line_07_mochi.wav"; Rate=-1; Text="아... 인사였구나." }
)

foreach ($line in $lines) {
  $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $voice = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq "ko-KR" } | Select-Object -First 1
  if ($voice) { $synth.SelectVoice($voice.VoiceInfo.Name) }
  $synth.Rate = $line.Rate
  $synth.Volume = 100
  $path = Join-Path $OutDir $line.File
  $synth.SetOutputToWaveFile($path)
  $synth.Speak($line.Text)
  $synth.Dispose()
}

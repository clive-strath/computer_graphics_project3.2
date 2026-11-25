Add-Type -AssemblyName System.Speech
$out = Join-Path $PSScriptRoot "voices"
New-Item -ItemType Directory -Force $out | Out-Null
$lines = @(
  @("R1", "Microsoft David Desktop", 0,  "...and that's the weather. Clear skies all week. Stay safe out there, folks."),
  @("M1", "Microsoft Zira Desktop", -1, "Stay safe. From what? Nothing ever happens here."),
  @("M2", "Microsoft Zira Desktop", 1,  "No. No, no, no..."),
  @("R2", "Microsoft David Desktop", -1, "...do not go outside... repeat... do not..."),
  @("M3", "Microsoft Zira Desktop", 3,  "Open, please, anyone, open the door!"),
  @("M4", "Microsoft Zira Desktop", 0,  "Think. Think..."),
  @("M5", "Microsoft Zira Desktop", -3, "I thought we had more time."),
  @("M6", "Microsoft Zira Desktop", -2, "If you're watching this... be careful. Always listen to the warnings."),
  @("M7", "Microsoft Zira Desktop", -2, "Bye."),
  @("M8", "Microsoft Zira Desktop", -3, "Goodbye.")
)
foreach ($l in $lines) {
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $s.SelectVoice($l[1])
  $s.Rate = $l[2]
  $fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(44100, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
  $s.SetOutputToWaveFile((Join-Path $out ($l[0] + ".wav")), $fmt)
  $s.Speak($l[3])
  $s.Dispose()
  Write-Output ("VOICE " + $l[0])
}

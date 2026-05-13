param (
    [Parameter(Position=0)]
    [string]$Text1,

    [Parameter()]
    [string]$InputJson
)

# Формируем список задач на печать (можно передать старым способом просто $Text1, либо новым массивом JSON)
$PrintJobs = @()
if ($InputJson) {
    $PrintJobs = $InputJson | ConvertFrom-Json
} elseif ($Text1) {
    # Разбиваем строку по запятым, точкам с запятой или пробелам (регулярное выражение)
    $numbers = $Text1 -split "[,;\s]+"
    foreach ($num in $numbers) {
        $cleanNum = $num.Trim()
        if ($cleanNum -ne "") {
            $PrintJobs += [PSCustomObject]@{ Label = $cleanNum; BarCode = $cleanNum }
        }
    }
} else {
    Write-Output "No input provided."
    exit
}

$Printers = New-Object -ComObject bpac.Printer
$TargetPrinter = "Brother QL-810W"

# Умный поиск принтера (вместо индекса [0])
if (-not $Printers.IsPrinterSupported($TargetPrinter)) {
    Write-Output "Error: Printer '$TargetPrinter' is not supported or not installed."
    exit
}

$LabelDoc = New-Object -ComObject bpac.Document
$Filename = Join-Path -Path $PSScriptRoot -ChildPath 'Label.lbx'

If ($LabelDoc.Open($Filename)) {
    try {
        # Привязываем конкретный принтер по имени
        $LabelDoc.SetPrinter($TargetPrinter, 0)

        # Открываем "канал" печати 1 раз (Пакетная печать)
        $LabelDoc.StartPrint('Batch Labels', 0)

        foreach ($Job in $PrintJobs) {
            # Подставляем разные значения в разные поля (имя сотрудника, инвентарник и т.д.)
            $lblObj = $LabelDoc.GetObject('Label')
            if ($null -ne $lblObj -and $Job.Label) { $lblObj.Text = $Job.Label }

            $bcObj = $LabelDoc.GetObject('BarCode')
            if ($null -ne $bcObj -and $Job.BarCode) { $bcObj.Text = $Job.BarCode }

            # Печатаем 1 копию и идем дальше по циклу (без переподключения к принтеру)
            $LabelDoc.PrintOut(1, 0)
        }

        # Закрываем "канал" печати
        $LabelDoc.EndPrint()
        $LabelDoc.Close()

        Write-Output "Successfully printed $($PrintJobs.Count) labels."
    } catch {
        Write-Output 'Failed printing'
        Write-Output $LabelDoc.ErrorCode
    }
} Else {
    Write-Output 'Failed to open label file'
}

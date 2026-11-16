# u-värdeberäknare
Richards U-värde-och fuktberäkningsprogam

## Installation

Install the required Python packages with the same Python interpreter used to
launch the application:

```powershell
python -m pip install -r requirements.txt
```

If Word export reports that `pdf2docx` is missing, use the interpreter and
install command shown in the error message. Multiple Python installations may
cause `python -m pip` to target a different environment than the application.

The report buttons can create PDF reports and editable Word (`.docx`) versions.
Word reports are converted from the corresponding PDF report to preserve its
content and layout as closely as possible.

import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

def procesar_conciliacion_completa(excel_file):
    xls = pd.ExcelFile(excel_file)

    bancos = pd.read_excel(xls, sheet_name='COMPILADO BANCOS')
    ingresos = pd.read_excel(xls, sheet_name='INGRESOS XML')
    egresos = pd.read_excel(xls, sheet_name='EGRESOS XML')
    comp_ingresos = pd.read_excel(xls, sheet_name='COMPLEMENTOS INGRESOS XML')
    comp_egresos = pd.read_excel(xls, sheet_name='COMPLEMENTOS EGRESOS XML')

    conciliado = []

    # Simplificación: convertir fechas
    bancos['FECHA'] = pd.to_datetime(bancos['FECHA'], errors='coerce')
    comp_ingresos['FechaPago'] = pd.to_datetime(comp_ingresos['FechaPago'], errors='coerce')

    # Ejemplo: agrupar complementos por UUID
    comp_grouped = comp_ingresos.groupby('UUID')
    for uuid, grupo in comp_grouped:
        fecha_pago = grupo['FechaPago'].iloc[0]
        monto_pagado = grupo['ImpPagado'].sum()
        folios = grupo['folio relacionado'].dropna().unique()
        receptor = grupo['Nombre Receptor'].iloc[0]

        # Buscar abonos bancarios en ventana de 2 meses desde fecha de pago
        ventana = bancos[
            (bancos['FECHA'] >= fecha_pago) & 
            (bancos['FECHA'] <= fecha_pago + pd.DateOffset(months=2)) & 
            (bancos['CARGO'].isna())
        ]

        # Buscar combinaciones que sumen al ImpPagado (simplificado aquí por igualdad directa)
        match = ventana[ventana['ABONO'].round(2) == round(monto_pagado, 2)]
        if not match.empty:
            conciliado.append({
                'UUID': uuid,
                'Fecha Pago': fecha_pago.date(),
                'Monto Complemento': monto_pagado,
                'Folio Relacionado': ', '.join(folios),
                'Receptor': receptor,
                'Movimientos Conciliados': len(match),
                'Monto Conciliado': match['ABONO'].sum()
            })

    # Exportar a Excel
    df_conciliado = pd.DataFrame(conciliado)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        bancos.to_excel(writer, sheet_name='COMPILADO BANCOS', index=False)
        ingresos.to_excel(writer, sheet_name='INGRESOS XML', index=False)
        egresos.to_excel(writer, sheet_name='EGRESOS XML', index=False)
        comp_ingresos.to_excel(writer, sheet_name='COMPLEMENTOS INGRESOS XML', index=False)
        comp_egresos.to_excel(writer, sheet_name='COMPLEMENTOS EGRESOS XML', index=False)
        df_conciliado.to_excel(writer, sheet_name='CONCILIACION INGRESOS', index=False)

    output.seek(0)
    return output
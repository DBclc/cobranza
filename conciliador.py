import pandas as pd
from io import BytesIO

def procesar_conciliacion_completa(excel_file):
    xls = pd.ExcelFile(excel_file)

    bancos = pd.read_excel(xls, sheet_name='COMPILADO BANCOS')
    ingresos = pd.read_excel(xls, sheet_name='INGRESOS XML')
    egresos = pd.read_excel(xls, sheet_name='EGRESOS XML')
    comp_ingresos = pd.read_excel(xls, sheet_name='COMPLEMENTOS INGRESOS XML')
    comp_egresos = pd.read_excel(xls, sheet_name='COMPLEMENTOS EGRESOS XML')

    bancos['fecha'] = pd.to_datetime(bancos['fecha'], errors='coerce')
    comp_ingresos['FechaPago'] = pd.to_datetime(comp_ingresos['FechaPago'], errors='coerce')
    comp_egresos['FechaPago'] = pd.to_datetime(comp_egresos['FechaPago'], errors='coerce')

    conciliado_ingresos = []
    conciliado_egresos = []

    # INGRESOS - Agrupación por UUID
    for uuid, grupo in comp_ingresos.groupby('UUID'):
        fecha_pago = grupo['FechaPago'].iloc[0]
        monto_pagado = grupo['ImpPagado'].sum()
        folios = grupo['folio relacionado'].dropna().unique()
        receptor = grupo['Nombre Receptor'].iloc[0]

        ventana = bancos[
            (bancos['fecha'] >= fecha_pago) &
            (bancos['fecha'] <= fecha_pago + pd.DateOffset(months=2)) &
            (bancos['cargos'].isna())
        ]
        match = ventana[ventana['abonos'].round(2) == round(monto_pagado, 2)]
        if not match.empty:
            conciliado_ingresos.append({
                'Tipo': 'Ingreso',
                'UUID': uuid,
                'Fecha Pago': fecha_pago.date(),
                'Monto Complemento': monto_pagado,
                'Folio Relacionado': ', '.join(folios),
                'Nombre Receptor': receptor,
                'Movimientos Conciliados': len(match),
                'Monto Conciliado': match['abonos'].sum()
            })

    # EGRESOS - Agrupación por UUID
    for uuid, grupo in comp_egresos.groupby('UUID'):
        fecha_pago = grupo['FechaPago'].iloc[0]
        monto_pagado = grupo['ImpPagado'].sum()
        folios = grupo['FolioRel'].dropna().unique()
        emisor = grupo['Nombre Emisor'].iloc[0]

        ventana = bancos[
            (bancos['fecha'] >= fecha_pago) &
            (bancos['fecha'] <= fecha_pago + pd.DateOffset(months=2)) &
            (bancos['abonos'].isna())
        ]
        match = ventana[ventana['cargos'].round(2) == round(monto_pagado, 2)]
        if not match.empty:
            conciliado_egresos.append({
                'Tipo': 'Egreso',
                'UUID': uuid,
                'Fecha Pago': fecha_pago.date(),
                'Monto Complemento': monto_pagado,
                'Folio Relacionado': ', '.join(folios),
                'Nombre Emisor': emisor,
                'Movimientos Conciliados': len(match),
                'Monto Conciliado': match['cargos'].sum()
            })

    df_conc_ingresos = pd.DataFrame(conciliado_ingresos)
    df_conc_egresos = pd.DataFrame(conciliado_egresos)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        bancos.to_excel(writer, sheet_name='COMPILADO BANCOS', index=False)
        ingresos.to_excel(writer, sheet_name='INGRESOS XML', index=False)
        egresos.to_excel(writer, sheet_name='EGRESOS XML', index=False)
        comp_ingresos.to_excel(writer, sheet_name='COMPLEMENTOS INGRESOS XML', index=False)
        comp_egresos.to_excel(writer, sheet_name='COMPLEMENTOS EGRESOS XML', index=False)
        df_conc_ingresos.to_excel(writer, sheet_name='CONCILIACION INGRESOS', index=False)
        df_conc_egresos.to_excel(writer, sheet_name='CONCILIACION EGRESOS', index=False)

    output.seek(0)
    return output

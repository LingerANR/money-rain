# Investment Platform Lab: Negative Amount Manipulation

Laboratorio vulnerable diseñado para demostrar cómo una falla de lógica de negocio puede comprometer la integridad de transacciones financieras mediante la manipulación de montos negativos.

## Servicios

```bash
docker compose up --build
```

* Banco: `http://localhost:5001`
* Plataforma de inversiones: `http://localhost:5000`

## Escenario

El laboratorio simula la interacción entre dos aplicaciones independientes:

* Un **Banco**, encargado de administrar cuentas bancarias.
* Una **Plataforma de inversiones**, donde los usuarios pueden depositar y retirar fondos.

El flujo esperado es sencillo:

1. El usuario transfiere dinero desde el banco hacia la plataforma de inversiones.
2. La plataforma registra el depósito.
3. Posteriormente, el usuario puede retirar fondos de regreso al banco.

La vulnerabilidad ocurre durante el proceso de retiro.

## La vulnerabilidad

El backend no valida que el monto solicitado sea estrictamente mayor a cero.

Como resultado, es posible enviar valores negativos durante una operación de retiro, alterando el flujo financiero previsto y generando movimientos que nunca deberían ser permitidos.

## Demo de ataque con Burp Suite

Objetivo: manipular una transacción utilizando un monto negativo.

1. Configura el navegador para utilizar Burp Suite.
2. Accede a la plataforma de inversiones.
3. Realiza un depósito legítimo desde el banco.
4. Dirígete a la función de retiro.
5. Activa **Intercept** en Burp.
6. Envía una solicitud de retiro válida.
7. Antes de reenviar la petición, modifica el parámetro `amount`.

Ejemplo:

```json
{
  "amount": -300
}
```

8. Reenvía la solicitud.
9. Observa cómo el sistema procesa una operación que viola las reglas de negocio esperadas.

Resultado: la integridad de las transacciones queda comprometida debido a una validación insuficiente del monto.

## Ejemplo con curl

Retiro manipulando el monto:

```bash
curl -X POST http://localhost:5000/api/withdraw \
  -H "Content-Type: application/json" \
  -d '{"amount": -300}'
```

## ¿Por qué es vulnerable?

La aplicación asume que todos los montos recibidos serán positivos.

Sin embargo, esa regla nunca es validada por el backend. Un atacante puede abusar de esta omisión para ejecutar operaciones financieras no contempladas durante el diseño del sistema.

Este tipo de fallas suele clasificarse como una **Business Logic Vulnerability**, cuya causa raíz es una validación insuficiente de entradas.

## Mitigación correcta

Antes de procesar cualquier operación financiera, el backend debe validar que:

* El monto sea estrictamente mayor que cero.
* El usuario disponga de saldo suficiente.
* La operación respete todas las reglas de negocio definidas.
* Se registren eventos anómalos para su posterior análisis.
* Existan alertas ante comportamientos financieros inusuales.

Por ejemplo:

```python
if amount <= 0:
    return {"error": "Invalid amount"}, 400
```

## Archivo vulnerable

La validación intencionalmente ausente se encuentra en la lógica encargada de procesar los retiros.

El objetivo del laboratorio es que el estudiante identifique el defecto, comprenda su impacto y proponga una corrección adecuada.

## Reset del laboratorio

Para restaurar el estado inicial:

```bash
curl -X POST http://localhost:5000/api/reset-all
```

o reinicia los contenedores:

```bash
docker compose down
docker compose up --build
```

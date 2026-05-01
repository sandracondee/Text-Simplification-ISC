import asyncio
from dotenv import load_dotenv
load_dotenv()
from src.mcp.mcp_manager import mcp_manager



async def main():
    print("🔌 Conectando al servidor MCP local...")

    try:
        tools = await mcp_manager.get_tools_for_agent(["metrics_server"])
        print(f"Conexión exitosa. Herramientas disponibles: {[t.name for t in tools]}")
        
        calc_tool = next((t for t in tools if t.name == "calculate_metrics"), None)
        
        if not calc_tool:
            print("Error: No se encontró la herramienta 'calculate_metrics' en el servidor.")
            return

        print("\nInvocando la herramienta calculate_metrics con parámetros de prueba.")
        
        parametros_prueba = {
            "complex_text": "El paciente presenta un cuadro de cefalea aguda.",
            "current_simplified_text": "El paciente tiene un dolor de cabeza fuerte.",
            "reference_text": "El paciente sufre de dolor de cabeza severo."
        }
        
        resultado = await calc_tool.ainvoke(parametros_prueba)
        
        print("\nResultado devuelto por el servidor:")
        import json
        print(json.dumps(resultado, indent=2))
        
    except Exception as e:
        print(f"\nOcurrió un error de conexión o ejecución: {e}")
        
if __name__ == "__main__":
    asyncio.run(main())
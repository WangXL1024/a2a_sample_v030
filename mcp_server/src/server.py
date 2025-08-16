import asyncio
from fastmcp import FastMCP
from fastmcp.tools import tool
from src.services.loan_suggest import LoanSuggestService
from src.services.loan_pre_examination import LoanPreExaminationService
from typing import Dict, Optional

mcp = FastMCP("auto_finance_mcp")

@mcp.tool()
async def get_loan_scheme_from_rag(model_id: Optional[str] = None) -> Dict:
    # """对外暴露的贷款方案查询接口（调用封装好的 LoanSuggestService）"""
    return await LoanSuggestService.get_loan_scheme(model_id)

@mcp.tool()
async def get_credit_info(id_number:str) -> Dict:
    # """对外暴露的信用报告查询接口（调用封装好的 CreditReportingService）"""
    return await LoanPreExaminationService.get_credit_info(id_number)

@mcp.tool()
async def create_examination_result(id_number:str,phone_number:str,result:str):
    # """对外暴露的信用报告查询接口（调用封装好的 CreditReportingService）"""
    await LoanPreExaminationService.create_examination_result(id_number,phone_number,result)

async def main():
    await mcp.run_streamable_http_async(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from pymongo import MongoClient
from datetime import datetime

# 定义返回结果的数据模型
class CreditInfoResult(BaseModel):
    id_number: str
    credit_report: List[str] = Field(default_factory=list)
    error: Optional[str] = None
# 连接MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['bmw_credit_db']
credit_collection = db['credit_information']
examination_result_collection = db['examination_result']

class LoanPreExaminationService:
    """Encapsulate the RAG query logic of the existing auto loan scheme"""
    
    @staticmethod
    async def get_credit_info(id_number: str) -> Dict:
        """
        Query the user's credit information based on the ID card number.
        Args:
            id_number: ID card number
        Returns: 
            the user's credit information
        """
        try:
            if not id_number:
                return CreditInfoResult(
                    id_number="",
                    error="身份证号不能为空"
                ).model_dump()
            
            # 从MongoDB查询数据
            credit_info = credit_collection.find_one({"id_number": id_number})
            
            if not credit_info:
                return CreditInfoResult(
                    id_number=id_number,
                    error="未查询到该身份证号的征信信息"
                ).model_dump()
            
            # 构建征信报告内容列表
            credit_report = []
            
            # 添加基本信息
            credit_report.append(f"用户姓名: {credit_info.get('user_name', '未知')}")
            credit_report.append(f"联系电话: {credit_info.get('phone_number', '未知')}")
            credit_report.append(f"征信状态: {'良好' if credit_info.get('credit_status') == 'good' else '不良'}")
            credit_report.append("--- 信用记录详情 ---")
            
            # 遍历信用记录
            for idx, record in enumerate(credit_info.get('credit_records', []), 1):
                record_type = "信用卡" if record['type'] == 'credit_card' else "贷款"
                status = "正常" if not record['overdue_records'] else "存在逾期"
                
                record_str = (f"{idx}. {record_type} - {record['institution']}\n"
                            f"   起止日期: {record['start_date']} 至 {record['end_date'] or '至今'}\n"
                            f"   状态: {status}")
                credit_report.append(record_str)
                
                # 添加逾期记录详情
                if record['overdue_records']:
                    for overdue in record['overdue_records']:
                        overdue_str = (f"   逾期记录: {overdue['date']}，逾期{overdue['days']}天，"
                                    f"金额{overdue['amount']}元")
                        credit_report.append(overdue_str)
            
            return CreditInfoResult(
                id_number=id_number,
                credit_report=credit_report
            ).model_dump()
            
        except Exception as e:
            return CreditInfoResult(
                id_number=id_number if id_number else "",
                error=f"查询失败: {str(e)}"
            ).model_dump()
        
    @staticmethod
    async def create_examination_result(id_number:str,phone_number:str,result:str) -> Dict:
        """
        Create the examination result after Pre-examination.
        Args:
            id_number: ID card number
            phone_number: phone number
            result: the result of the examination (e.g., "passed" or "unpassed")
        """
        try:
            examination_result_collection.insert_one({
                "id_number": id_number,
                "phone_number": phone_number,
                "examination_result": result,
                "examination_time": datetime.now().isoformat()
            })
        except Exception as e:
            return {"error": f"创建预审结果失败: {str(e)}"}
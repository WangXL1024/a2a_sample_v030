from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from pymongo import MongoClient
from datetime import datetime
from pymongo.errors import(
    ConnectionFailure,
    OperationFailure
)
import logging.config
import os

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path, encoding='utf-8')
logger = logging.getLogger(__name__)

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
            logger.info(f"开始查询身份证号为 {id_number} 的征信信息")
            if not id_number:
                logger.error("身份证号不能为空")
                return CreditInfoResult(
                    id_number="",
                    error="身份证号不能为空"
                ).model_dump()
            
            # 从MongoDB查询数据
            logger.debug(f"正在查询MongoDB中的数据，条件: {{'id_number': '{id_number}'}}")
            credit_info = credit_collection.find_one({"id_number": id_number})
            logger.debug(f"查询结果: {credit_info}")
            
            if not credit_info:
                logger.error(f"未查询到该身份证号的征信信息")
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
            
            logger.info(f"成功获取身份证号为 {id_number} 的征信信息")
            return CreditInfoResult(
                id_number=id_number,
                credit_report=credit_report
            ).model_dump()
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB连接失败: {str(e)}")
            return CreditInfoResult(
                id_number=id_number if id_number else "",
                error=f"MongoDB连接失败: {str(e)}"
            ).model_dump()
        except OperationFailure as e:
            logger.error(f"MongoDB操作失败: {str(e)}")
            return CreditInfoResult(
                id_number=id_number if id_number else "",
                error=f"MongoDB操作失败: {str(e)}"
            ).model_dump()
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
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
            logger.info(f"开始创建身份证号为 {id_number} 的预审结果")
            examination_result_collection.insert_one({
                "id_number": id_number,
                "phone_number": phone_number,
                "examination_result": result,
                "examination_time": datetime.now().isoformat()
            })
            logger.info(f"成功创建身份证号为 {id_number} 的预审结果")
        except ConnectionFailure as e:
            logger.error(f"MongoDB连接失败: {str(e)}")
            return {"error": f"MongoDB连接失败: {str(e)}"}
        except OperationFailure as e:
            logger.error(f"MongoDB操作失败: {str(e)}")
            return {"error": f"MongoDB操作失败: {str(e)}"}
        except Exception as e:
            logger.error(f"创建预审结果失败: {str(e)}")
            return {"error": f"创建预审结果失败: {str(e)}"}
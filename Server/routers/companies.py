"""
Company management router.

Handles company CRUD operations.
"""

import maplex
from fastapi import APIRouter

import BaseModelData as BMD
from datadomain import CompanyManager

logger = maplex.Logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["companies"])


@router.post("/company", response_model=BMD.PostCompanyResponse)
def postCompanyInfo(item: BMD.PostCompanyRequestItem):

    logger.info(f"Post company info request received: {item.model_dump()}")
    retItem = BMD.PostCompanyResponse()

    try:

        companyManager = CompanyManager(item.Token)
        retItem = companyManager.createCompany(
            item.CompanyName,
            item.ContractLevel,
            item.CompanyPhone,
            item.CompanyZipCode,
            item.CompanyAddress,
            item.CompanyEmail
            )

    except Exception as e:

        logger.ShowError(e, "Failed to post company information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'companyManager' in locals():

            companyManager.close()

    return retItem


@router.get("/company", response_model=BMD.GetCompanyInfoResponse)
def getCompanyInfo(item: BMD.GetCompanyInfoRequestItem):

    logger.info(f"Get company info request received: {item.model_dump()}")
    retItem = BMD.GetCompanyInfoResponse()

    try:

        companyManager = CompanyManager(item.Token)
        retDict = companyManager.getCompanyList(str,item.CompanyID, item.CompanyName, item.ContractLevel)

        # Break down company list

        for company in retDict["CompanyList"]:

            companyItem = BMD.CompanyInfoResponseItem()
            companyItem.CompanyID = company[0]
            companyItem.CompanyName = company[1]
            companyItem.CompanyPhone = company[2]
            companyItem.CompanyZipCode = company[3]
            companyItem.CompanyAddress = company[4]
            companyItem.CompanyEmail = company[5]
            companyItem.ContractLevel = company[6]

            retItem.Companies.append(companyItem)

        retItem.ErrorInfo = BMD.errorInfo(**retDict["ErrorInfo"])

    except Exception as e:

        logger.ShowError(e, "Failed to get company information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'companyManager' in locals():

            companyManager.close()

    return retItem

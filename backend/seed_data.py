"""初始化种子数据：插入保险公司机构、指标定义、默认管理员"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models import SysUser, SysRole, IalmdBankInstitution, IalmdIndicatorDefine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 保险公司数据（覆盖上市险企 + 头部财险/寿险/再保险/健康险/养老险）
INSURANCE_COMPANIES = [
    # 保险集团（上市）
    ("中国平安保险(集团)股份有限公司", "中国平安", "PINGAN", "GROUP", "601318", "A+H"),
    ("中国人寿保险(集团)公司", "中国人寿", "CHINALIFE", "GROUP", "601628", "A+H"),
    ("中国太平洋保险(集团)股份有限公司", "中国太保", "CPIC", "GROUP", "601601", "A+H"),
    ("中国人民保险集团股份有限公司", "中国人保", "PICC", "GROUP", "601319", "A+H"),
    ("中国太平保险集团有限责任公司", "中国太平", "CHINATAIPING", "GROUP", "0966", "H"),
    ("阳光保险集团股份有限公司", "阳光保险", "SUNSHINE", "GROUP", "6963", "H"),
    # 寿险公司
    ("中国人寿保险股份有限公司", "中国人寿股份", "CHINALIFE_L", "LIFE", "601628", "A+H"),
    ("新华人寿保险股份有限公司", "新华保险", "NCI", "LIFE", "601336", "A+H"),
    ("泰康人寿保险有限责任公司", "泰康人寿", "TAIKANG_LIFE", "LIFE", "", "UNLISTED"),
    ("友邦人寿保险有限公司", "友邦人寿", "AIA", "LIFE", "1299", "H"),
    ("太平人寿保险有限公司", "太平人寿", "TAIPING_LIFE", "LIFE", "", "UNLISTED"),
    ("中邮人寿保险股份有限公司", "中邮人寿", "POSTAL_LIFE", "LIFE", "", "UNLISTED"),
    ("国华人寿保险股份有限公司", "国华人寿", "GUOHUA_LIFE", "LIFE", "000627", "A"),
    # 财险公司
    ("中国人民财产保险股份有限公司", "人保财险", "PICC_PNC", "PNC", "2328", "H"),
    ("中国平安财产保险股份有限公司", "平安产险", "PINGAN_PNC", "PNC", "", "UNLISTED"),
    ("中国太平洋财产保险股份有限公司", "太保产险", "CPIC_PNC", "PNC", "", "UNLISTED"),
    ("中国人寿财产保险股份有限公司", "国寿财险", "CL_PNC", "PNC", "", "UNLISTED"),
    ("中华联合财产保险股份有限公司", "中华联合财险", "CHINAUNION_PNC", "PNC", "", "UNLISTED"),
    ("中国大地财产保险股份有限公司", "大地保险", "CCIC_PNC", "PNC", "", "UNLISTED"),
    ("众安在线财产保险股份有限公司", "众安在线", "ZHONGAN", "PNC", "6060", "H"),
    # 再保险公司
    ("中国再保险(集团)股份有限公司", "中国再保险", "CHINARE", "REINSURANCE", "1508", "H"),
    ("中国财产再保险有限责任公司", "中再产险", "CHINARE_PNC", "REINSURANCE", "", "UNLISTED"),
    ("瑞士再保险股份有限公司北京分公司", "瑞再", "SWISSRE", "REINSURANCE", "", "UNLISTED"),
    ("慕尼黑再保险公司北京分公司", "慕再", "MUNICHRE", "REINSURANCE", "", "UNLISTED"),
    # 健康险公司
    ("平安健康保险股份有限公司", "平安健康", "PINGAN_HEALTH", "HEALTH", "1833", "H"),
    ("中国人民健康保险股份有限公司", "人保健康", "PICC_HEALTH", "HEALTH", "", "UNLISTED"),
    ("昆仑健康保险股份有限公司", "昆仑健康", "KUNLUN_HEALTH", "HEALTH", "", "UNLISTED"),
    # 养老险公司
    ("平安养老保险股份有限公司", "平安养老", "PINGAN_PENSION", "PENSION", "", "UNLISTED"),
    ("泰康养老保险股份有限公司", "泰康养老", "TAIKANG_PENSION", "PENSION", "", "UNLISTED"),
    ("长江养老保险股份有限公司", "长江养老", "CJ_PENSION", "PENSION", "", "UNLISTED"),
]

# 保险指标定义（7 大类 20 个核心指标）
INDICATORS = [
    # 规模指标
    ("TOTAL_ASSETS", "总资产", "资产总计,资产总额", "SCALE", "亿元", 2, "总资产 = 负债 + 所有者权益", 1),
    ("NET_ASSETS", "净资产", "所有者权益,股东权益", "SCALE", "亿元", 2, "净资产 = 总资产 - 总负债", 2),
    ("GPW", "原保费收入", "原保险保费收入,保险业务收入,保费收入", "SCALE", "亿元", 2, "原保险保费收入", 3),
    ("NET_PROFIT", "净利润", "归属母公司股东净利润,归母净利润", "SCALE", "亿元", 2, "", 4),
    # 盈利指标
    ("ROE", "净资产收益率", "资本利润率,ROE,加权平均净资产收益率", "PROFIT", "%", 2, "ROE = 净利润 / 平均净资产 × 100%", 5),
    ("TOTAL_INVEST_YIELD", "总投资收益率", "投资收益率,综合投资收益率", "PROFIT", "%", 2, "总投资收益率 = 总投资收益 / 平均投资资产 × 100%", 6),
    ("NET_INVEST_YIELD", "净投资收益率", "净投资收益率", "PROFIT", "%", 2, "净投资收益率 = 净投资收益 / 平均投资资产 × 100%", 7),
    # 偿付能力指标（保险核心）
    ("CORE_SOLVENCY", "核心偿付能力充足率", "核心偿付能力,核心偿付能力溢额率", "SOLVENCY", "%", 2, "核心偿付能力充足率 = 核心资本 / 最低资本 × 100%（监管≥50%）", 8),
    ("COMP_SOLVENCY", "综合偿付能力充足率", "综合偿付能力,偿付能力充足率", "SOLVENCY", "%", 2, "综合偿付能力充足率 = 实际资本 / 最低资本 × 100%（监管≥100%）", 9),
    ("ACTUAL_CAPITAL", "实际资本", "认可资本,实际偿付能力额度", "SOLVENCY", "亿元", 2, "实际资本 = 认可资产 - 认可负债", 10),
    ("MIN_CAPITAL", "最低资本", "最低偿付能力额度,量化风险最低资本", "SOLVENCY", "亿元", 2, "偿二代量化风险最低资本要求", 11),
    # 业务质量指标
    ("COR", "综合成本率", "综合成本比率,承保综合成本率", "QUALITY", "%", 2, "综合成本率 = 赔付率 + 费用率（财险，<100%为承保盈利）", 12),
    ("LOSS_RATIO", "赔付率", "综合赔付率,赔付支出率", "QUALITY", "%", 2, "赔付率 = 赔付支出 / 已赚保费 × 100%", 13),
    ("SURRENDER_RATE", "退保率", "保单退保率,综合退保率", "QUALITY", "%", 2, "退保率 = 退保金 / 期初责任准备金 × 100%（寿险）", 14),
    ("PERSISTENCY_13M", "13个月继续率", "13个月保费继续率,续期率", "QUALITY", "%", 2, "13个月继续率 = 13个月后仍有效保单保费 / 首年保费", 15),
    # 价值指标（保险特有）
    ("NBV", "新业务价值", "NBV,新业务内含价值", "VALUE", "亿元", 2, "新业务价值 = 新承保业务未来利润现值", 16),
    ("EV", "内含价值", "EV,内含价值,内含价值总额", "VALUE", "亿元", 2, "内含价值 = 存量业务价值 + 调整后净资产", 17),
    # 渠道指标
    ("AGENT_COUNT", "代理人数量", "个险代理人,营销员数量,代理人总数", "CHANNEL", "万人", 2, "", 18),
    # ESG指标
    ("GREEN_INSURANCE", "绿色保险保费收入", "绿色保险,绿色保费", "ESG", "亿元", 2, "", 19),
    ("GREEN_INVEST", "绿色投资规模", "绿色投资,ESG投资", "ESG", "亿元", 2, "", 20),
]


def seed():
    db = SessionLocal()
    try:
        # 1. 创建角色
        roles_data = [
            ("ADMIN", "系统管理员", 1),
            ("MANAGER", "部门负责人", 2),
            ("SENIOR_ANALYST", "高级分析师", 3),
            ("ANALYST", "分析师", 4),
            ("ADVISOR", "顾问", 5),
        ]
        for code, name, order in roles_data:
            if not db.query(SysRole).filter(SysRole.role_code == code).first():
                db.add(SysRole(role_name=name, role_code=code, sort_order=order))
        db.flush()

        # 2. 创建管理员用户 (password: admin123)
        admin_role = db.query(SysRole).filter(SysRole.role_code == "ADMIN").first()
        if not db.query(SysUser).filter(SysUser.username == "admin").first():
            admin = SysUser(
                username="admin",
                password_hash=pwd_context.hash("admin123"),
                real_name="系统管理员",
                email="admin@ialmd.local",
            )
            db.add(admin)
        db.flush()

        # 3. 插入保险公司机构
        for name, short, code, btype, stock, market in INSURANCE_COMPANIES:
            exists = db.query(IalmdBankInstitution).filter(
                IalmdBankInstitution.bank_code == code
            ).first()
            if not exists:
                db.add(IalmdBankInstitution(
                    bank_name=name,
                    short_name=short,
                    bank_code=code,
                    bank_type=btype,
                    stock_code=stock,
                    listing_market=market,
                ))
        db.flush()

        # 4. 插入指标定义
        for code, name, alias, cat, unit, decimals, formula, order in INDICATORS:
            exists = db.query(IalmdIndicatorDefine).filter(
                IalmdIndicatorDefine.indicator_code == code
            ).first()
            if not exists:
                db.add(IalmdIndicatorDefine(
                    indicator_code=code,
                    indicator_name=name,
                    indicator_alias=alias,
                    category_code=cat,
                    unit=unit,
                    decimal_places=decimals,
                    calc_formula=formula,
                    sort_order=order,
                ))
        db.flush()

        db.commit()
        print("种子数据初始化完成！")
        print(f"  - 角色: {len(roles_data)} 个")
        print(f"  - 保险公司: {len(INSURANCE_COMPANIES)} 家")
        print(f"  - 指标: {len(INDICATORS)} 个")
        print(f"  - 管理员: admin / admin123")

    except Exception as e:
        db.rollback()
        print(f"种子数据初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

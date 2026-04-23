"""Seed the smb_advertisers table with 500 synthetic SMB records."""

import os
import sys
import logging
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from data.synthetic.generate_smbs import generate_smbs

load_dotenv()
console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INSERT_SQL = """
    INSERT INTO smb_advertisers (
        business_name, industry, sub_industry,
        country, state, city, dma_code, dma_name, zip_code,
        employee_count, annual_revenue_usd, business_age_years,
        advertising_experience, monthly_ad_spend_usd,
        has_run_meta_ads, last_meta_ad_date,
        facebook_page_followers, instagram_followers, has_website,
        primary_product_category, business_type, is_ecommerce,
        has_physical_location, lead_source, acquisition_likelihood_score
    ) VALUES (
        %(business_name)s, %(industry)s, %(sub_industry)s,
        %(country)s, %(state)s, %(city)s, %(dma_code)s, %(dma_name)s, %(zip_code)s,
        %(employee_count)s, %(annual_revenue_usd)s, %(business_age_years)s,
        %(advertising_experience)s, %(monthly_ad_spend_usd)s,
        %(has_run_meta_ads)s, %(last_meta_ad_date)s,
        %(facebook_page_followers)s, %(instagram_followers)s, %(has_website)s,
        %(primary_product_category)s, %(business_type)s, %(is_ecommerce)s,
        %(has_physical_location)s, %(lead_source)s, %(acquisition_likelihood_score)s
    )
    ON CONFLICT DO NOTHING
"""


def seed_smbs(database_url: str, n: int = 500) -> int:
    smbs = generate_smbs(n)
    conn = psycopg2.connect(database_url)
    inserted = 0
    try:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, INSERT_SQL, smbs, page_size=100)
            inserted = cur.rowcount if cur.rowcount > 0 else n
        conn.commit()
        logger.info(f"Inserted {inserted} SMB records")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to seed SMBs: {e}")
        raise
    finally:
        conn.close()

    # Summary
    from collections import Counter
    table = Table(title="SMB Advertiser Seed Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    table.add_row("Records generated", str(n))
    table.add_row("Unique industries", str(len(set(s["industry"] for s in smbs))))
    table.add_row("Unique DMAs", str(len(set(s["dma_code"] for s in smbs))))
    table.add_row("With Meta ads history", str(sum(s["has_run_meta_ads"] for s in smbs)))
    table.add_row("E-commerce businesses", str(sum(s["is_ecommerce"] for s in smbs)))
    table.add_row("Avg monthly ad spend", f"${sum(s['monthly_ad_spend_usd'] for s in smbs)/len(smbs):,.0f}")
    console.print(table)

    return inserted


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set")
        sys.exit(1)
    seed_smbs(db_url)

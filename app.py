import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# הגדרות עיצוב בסיסיות בעברית ויישור לימין
st.set_page_config(page_title="מערכת ניתוח מניות חכמה", layout="wide", initial_sidebar_state="expanded")

# פונקציית עזר לעיצוב מספרים גדולים (Billion, Million, Trillion)
def format_large_num(num):
    if num is None or pd.isna(num): return "N/A"
    if num >= 1e12: return f"${num/1e12:.2f}T"
    if num >= 1e9: return f"${num/1e9:.2f}B"
    if num >= 1e6: return f"${num/1e6:.2f}M"
    return f"${num:,.0f}"

# פונקציית עזר לעיצוב אחוזים
def format_pct(val):
    if val is None or pd.isna(val): return "N/A"
    return f"{val * 100:.2f}%" if val <= 1.0 else f"{val:.2f}%"

# כותרת ראשית
st.title("📊 מערכת לבחינת מניות בשוק ההון - גרסת פרו")

# תיבת קלט להזנת הטיקר
ticker = st.text_input("הכנס טיקר של מניה (למשל: AAPL, MSFT, NVDA, PANW):", "AAPL").upper().strip()

if ticker:
    with st.spinner('מושך נתונים מ-Yahoo Finance... אנא המתן'):
        try:
            # משיכת הנתונים מה-API עבור 5 שנים אחורה כבסיס
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # בדיקה שהטיקר תקין וקיים מידע
            if not info or 'longName' not in info:
                st.error(f"לא נמצאו נתונים עבור הטיקר: {ticker}. אנא ודא שהקשדת אותו נכון.")
                st.stop()
                
            financials = stock.financials         # דוח רווח והפסד
            balance_sheet = stock.balance_sheet   # מאזן
            cashflow = stock.cashflow             # תזרים מזומנים
            
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'לא ידוע')
            industry = info.get('industry', 'לא ידוע')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            st.subheader(f"חברה: {company_name} | סקטור: {sector} ({industry}) | מחיר נוכחי: ${current_price:.2f}")
            
            # יצירת הטאבים המופרדים
            tab1, tab2 = st.tabs(["🔍 ניתוח פנדמנטלי + תעודת זהות", "📈 ניתוח טכני (מלא)"])
            
            # ==========================================
            # טאב 1: ניתוח פנדמנטלי + גרף דינמי ותעודת זהות
            # ==========================================
            with tab1:
                # חלוקת המסך לעמודה של גרף (שמאל) ועמודה של תעודת זהות (ימין)
                col_graph, col_id = st.columns([2, 1])
                
                with col_graph:
                    st.subheader("📈 גרף ביצועי מניה מהיר")
                    
                    # כפתורי לחצנים לשינוי טווח הזמן של הגרף
                    timeframe = st.radio(
                        "בחר טווח זמן לגרף:",
                        ["1D", "5D", "1M", "6M", "1Y", "YTD", "3Y", "5Y"],
                        index=4, # ברירת מחדל 1Y
                        horizontal=True
                    )
                    
                    # מיפוי לחצנים להגדרות yfinance
                    tf_mapping = {
                        "1D": {"period": "1d", "interval": "5m"},
                        "5D": {"period": "5d", "interval": "15m"},
                        "1M": {"period": "1mo", "interval": "1d"},
                        "6M": {"period": "6mo", "interval": "1d"},
                        "1Y": {"period": "1y", "interval": "1d"},
                        "YTD": {"period": "ytd", "interval": "1d"},
                        "3Y": {"period": "3y", "interval": "1d"},
                        "5Y": {"period": "5y", "interval": "1d"}
                    }
                    
                    # משיכת נתוני הגרף הספציפי לפי הבחירה
                    opts = tf_mapping[timeframe]
                    df_fund_chart = stock.history(period=opts["period"], interval=opts["interval"])
                    
                    if not df_fund_chart.empty:
                        fig_fund = go.Figure()
                        # גרף קו רציף ונקי לניתוח מהיר בפנדמנטלי
                        fig_fund.add_trace(go.Scatter(
                            x=df_fund_chart.index, 
                            y=df_fund_chart['Close'], 
                            mode='lines', 
                            name='מחיר סגירה',
                            line=dict(color='#2ca02c', width=2)
                        ))
                        fig_fund.update_layout(
                            title=f"גרף מניית {ticker} - טווח {timeframe}",
                            xaxis_title="תאריך/זמן",
                            yaxis_title="מחיר ($)",
                            height=400,
                            margin=dict(l=20, r=20, t=40, b=20),
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_fund, use_container_width=True)
                    else:
                        st.warning("לא נמצאו נתוני מחיר לטווח הזמן שנבחר.")
                
                with col_id:
                    # תיקון שגיאת unsafe_index ל-unsafe_allow_html
                    st.markdown("<h3 style='text-align: right;'>🪪 תעודת זהות למניה</h3>", unsafe_allow_html=True)
                    
                    # --- חישובים וחילוץ נתונים עבור תעודת הזהות ---
                    market_cap = info.get('marketCap')
                    operating_cf = info.get('operatingCashflow')
                    
                    # P/CF חישוב
                    p_cf = (market_cap / operating_cf) if market_cap and operating_cf else info.get('priceToCashFlow')
                    
                    pe = info.get('trailingPE')
                    fwd_pe = info.get('forwardPE')
                    peg = info.get('pegRatio')
                    fwd_peg = info.get('forwardPegRatio', "N/A")
                    
                    # Yields חישוב (TTM)
                    earnings_yield = (1 / pe) * 100 if pe else None
                    cf_yield = (operating_cf / market_cap) * 100 if operating_cf and market_cap else None
                    
                    free_cash_flow = info.get('freeCashflow')
                    fcf_yield = (free_cash_flow / market_cap) * 100 if free_cash_flow and market_cap else None
                    
                    div_yield = info.get('dividendYield')
                    payout_ratio = info.get('payoutRatio')
                    
                    # Balances (MRQ)
                    total_cash = info.get('totalCash')
                    total_debt = info.get('totalDebt')
                    net_balance = (total_cash - total_debt) if total_cash is not None and total_debt is not None else None
                    
                    # Margins
                    gross_margin = info.get('grossMargins')
                    operating_margin = info.get('operatingMargins')
                    net_margin = info.get('profitMargins')
                    
                    # תצוגה ויזואלית של הנתונים
                    with st.container(border=True):
                        st.markdown("**💰 Financials**")
                        st.write(f"**Market Cap:** {format_large_num(market_cap)}")
                        st.write(f"**P/CF:** {f'{p_cf:.2f}' if p_cf else 'N/A'}")
                        st.write(f"**PE / FWD PE:** {f'{pe:.2f}' if pe else 'N/A'} / {f'{fwd_pe:.2f}' if fwd_pe else 'N/A'}")
                        st.write(f"**PEG / FWD PEG:** {f'{peg:.2f}' if peg else 'N/A'} / {f'{fwd_peg:.2f}' if isinstance(fwd_peg, float) else fwd_peg}")
                        
                        st.markdown("---")
                        st.markdown("**📈 Yields**")
                        st.write(f"**Earnings Yield (TTM):** {f'{earnings_yield:.2f}%' if earnings_yield else 'N/A'}")
                        st.write(f"**C/F Yield (TTM):** {f'{cf_yield:.2f}%' if cf_yield else 'N/A'}")
                        st.write(f"**FCF Yield (TTM):** {f'{fcf_yield:.2f}%' if fcf_yield else 'N/A'}")
                        st.write(f"**Dividend Yield (TTM):** {format_pct(div_yield)}")
                        st.write(f"**Payout Ratio (TTM):** {format_pct(payout_ratio)}")
                        
                        st.markdown("---")
                        st.markdown("**⚖️ Balances**")
                        st.write(f"**Total Cash (MRQ):** {format_large_num(total_cash)}")
                        st.write(f"**Total Debt:** {format_large_num(total_debt)}")
                        
                        # תיקון פוטנציאלי נוסף מ-st.write ל-st.markdown עבור HTML תקין
                        if net_balance and net_balance > 0:
                            st.markdown(f"**Net:** <span style='color:green;'>{format_large_num(net_balance)} (עודף מזומן)</span>", unsafe_allow_html=True)
                        elif net_balance:
                            st.markdown(f"**Net:** <span style='color:red;'>{format_large_num(net_balance)} (חוב נטו)</span>", unsafe_allow_html=True)
                        else:
                            st.write("**Net:** N/A")
                            
                        st.markdown("---")
                        st.markdown("**📊 Margins**")
                        st.write(f"**Gross Profit Margin:** {format_pct(gross_margin)}")
                        st.write(f"**Operating Margin:** {format_pct(operating_margin)}")
                        st.write(f"**Net Income Margin:** {format_pct(net_margin)}")

                st.write("---")
                
                # --- כרטיס הניקוד האוטומטי (Scorecard) ---
                st.subheader("📋 כרטיס ניקוד וחוקים אוטומטיים")
                
                roe = info.get('returnOnEquity')
                rev_growth = info.get('revenueGrowth')
                earnings_growth = info.get('earningsGrowth')
                current_ratio = info.get('currentRatio')
                debt_to_equity = info.get('debtToEquity')
                
                col_sc1, col_sc2 = st.columns(2)
                with col_sc1:
                    roe_text = f"{roe*100:.1f}%" if roe else "N/A"
                    if roe and roe >= 0.15:
                        st.success(f"✅ **תשואה על ההון (ROE):** {roe_text} (עומד ביעד של מעל 15%)")
                    else:
                        st.error(f"❌ **תשואה על ההון (ROE):** {roe_text} (מתחת ליעד של 15%)")
                        
                    if rev_growth and rev_growth > 0:
                        st.success(f"✅ **צמיחת הכנסות חיובית:** {rev_growth*100:.1f}%")
                    else:
                        st.error(f"❌ **אין צמיחת הכנסות או שהיא שלילית:** {f'{rev_growth*100:.1f}%' if rev_growth else 'N/A'}")
                        
                    if earnings_growth and rev_growth:
                        if earnings_growth > rev_growth:
                            st.success(f"✅ **צמיחת ה-EPS מהירה מההכנסות:** {earnings_growth*100:.1f}% מול {rev_growth*100:.1f}%")
                        else:
                            st.warning(f"⚠️ **צמיחת ה-EPS איטית מקצב צמיחת ההכנסות.**")
                
                with col_sc2:
                    if current_ratio and current_ratio >= 1:
                        st.success(f"✅ **יחס שוטף:** {current_ratio:.2f} (גדול מ-1, נזילות טובה לטווח קצר)")
                    else:
                        st.error(f"❌ **יחס שוטף:** {current_ratio if current_ratio else 'N/A'} (סיכון נזילות לטווח קצר)")
                        
                    if debt_to_equity:
                        leverage = debt_to_equity / 100
                        if leverage <= 1:
                            st.success(f"✅ **מנוף פיננסי (חוב להון):** {leverage:.2f} (קטן מ-1, רמה בריאה)")
                        else:
                            st.error(f"❌ **מנוף פיננסי (חוב להון):** {leverage:.2f} (גדול מ-1, מינוף גבוה)")
                            
                    if operating_cf and free_cash_flow:
                        fcf_to_ocf_ratio = free_cash_flow / operating_cf
                        growth_sectors = ['Technology', 'Technology Hardware', 'Semiconductors', 'Energy', 'Clean Energy']
                        is_growth_sector = any(sec.lower() in sector.lower() for sec in growth_sectors)
                        
                        if fcf_to_ocf_ratio >= 0.50:
                            st.success(f"✅ **תזרים חופשי מעולה:** {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל (מעל 50%)")
                        else:
                            if is_growth_sector:
                                st.warning(f"⚠️ **תזרים חופשי מהווה {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל.** המניה משתייכת לסקטור {sector} - הוצאות הוניות גבוהות (CapEx) נפוצות לצורך צמיחה וה-FCF מתכווץ זמנית.")
                            else:
                                st.error(f"❌ **תזרים חופשי נמוך:** {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל (מתחת ל-50%)")

            # ==========================================
            # טאב 2: ניתוח טכני מלא - 5 שנים אחורה
            # ==========================================
            with tab2:
                st.header(f"📉 ניתוח טכני מקיף (5 שנים היסטוריה) - {ticker}")
                
                df_tech = stock.history(period="5y", interval="1d")
                
                if df_tech.empty:
                    st.error("לא ניתן היה למשוך נתוני מחיר היסטוריים לניתוח הטכני.")
                else:
                    df_tech['SMA50'] = df_tech['Close'].rolling(window=50).mean()
                    df_tech['SMA200'] = df_tech['Close'].rolling(window=200).mean()
                    
                    fig_tech = go.Figure()
                    
                    fig_tech.add_trace(go.Candlestick(
                        x=df_tech.index,
                        open=df_tech['Open'],
                        high=df_tech['High'],
                        low=df_tech['Low'],
                        close=df_tech['Close'],
                        name='מחיר מניה'
                    ))
                    
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['SMA50'], mode='lines', name='SMA 50 (טווח קצר-בינוני)', line=dict(color='orange', width=1.5)))
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['SMA200'], mode='lines', name='SMA 200 (טווח ארוך)', line=dict(color='blue', width=1.5)))
                    
                    fig_tech.update_layout(
                        title=f"גרף נרות יפניים וממוצעים נעים (5 שנים) עבור {ticker}",
                        xaxis_title="תאריך",
                        yaxis_title="מחיר בדולר ($)",
                        xaxis_rangeslider_visible=True,
                        height=650,
                        template="plotly_white"
                    )
                    
                    st.plotly_chart(fig_tech, use_container_width=True)
                    
                    last_close = df_tech['Close'].iloc[-1]
                    st.write(f"**מחיר סגירה אחרון בדוח האחרון:** ${last_close:.2f}")

        except Exception as e:
            st.error(f"אירעה שגיאה בעיבוד הנתונים: {e}")
            st.info("חלק מהנתונים הפיננסיים המורכבים עשויים שלא להיות זמינים ב-Yahoo Finance עבור חברה זו.")

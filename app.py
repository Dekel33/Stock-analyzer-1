import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# הגדרות עיצוב בסיסיות בעברית ויישור לימין
st.set_page_config(page_title="מערכת ניתוח מניות חכמה", layout="wide", initial_sidebar_state="expanded")

# כותרת ראשית
st.title("📊 מערכת לבחינת מניות בשוק ההון")
st.write("ניתוח פנדמנטלי חכם וניתוח טכני מתקדם ישירות מהדפדפן")

# תיבת קלט להזנת הטיקר
ticker = st.text_input("הכנס טיקר של מניה (למשל: AAPL, MSFT, NVDA, PANW):", "AAPL").upper().strip()

if ticker:
    with st.spinner('מושך נתונים מ-Yahoo Finance... אנא המתן'):
        try:
            # משיכת הנתונים מה-API
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # בדיקה שהטיקר תקין וקיים מידע
            if not info or 'longName' not in info:
                st.error(f"לא נמצאו נתונים עבור הטיקר: {ticker}. אנא ודא שהקשדת אותו נכון.")
                st.stop()
                
            financials = stock.financials         # דוח רווח והפסד
            balance_sheet = stock.balance_sheet   # מאזן
            cashflow = stock.cashflow             # תזרים מזומנים
            
            # הצגת שם החברה והסקטור בחלק העליון
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'לא ידוע')
            industry = info.get('industry', 'לא ידוע')
            
            st.subheader(f"חברה: {company_name} | סקטור: {sector} ({industry})")
            
            # יצירת הטאבים המופרדים
            tab1, tab2 = st.tabs(["🔍 ניתוח פנדמנטלי", "📈 ניתוח טכני"])
            
            # ==========================================
            # טאב 1: ניתוח פנדמנטלי
            # ==========================================
            with tab1:
                st.header("📋 כרטיס ניקוד והערכת שווי (Scorecard)")
                
                # --- 1. הערכת שווי ויחסים (מאוחד) ---
                st.subheader("💰 הערכת שווי ויחסים פיננסיים")
                
                pe_ratio = info.get('trailingPE')
                forward_pe = info.get('forwardPE')
                peg_ratio = info.get('pegRatio')
                roe = info.get('returnOnEquity')
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("מכפיל רווח נוכחי (P/E)", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                with col2:
                    st.metric("מכפיל רווח עתידי (Forward P/E)", f"{forward_pe:.2f}" if forward_pe else "N/A")
                with col3:
                    st.metric("מכפיל PEG", f"{peg_ratio:.2f}" if peg_ratio else "N/A")
                with col4:
                    roe_text = f"{roe*100:.1f}%" if roe else "N/A"
                    if roe and roe >= 0.15:
                        st.metric("תשואה על ההון (ROE)", roe_text, "✅ עומד ביעד (>=15%)")
                    else:
                        st.metric("תשואה על ההון (ROE)", roe_text, "❌ מתחת ליעד (<15%)", delta_color="inverse")

                st.write("---")
                
                # --- 2. דוח רווח והפסד (צמיחה ושולי רווח) ---
                st.subheader("📈 דוח רווח והפסד ושולי רווח")
                
                gross_margin = info.get('grossMargins')
                operating_margin = info.get('operatingMargins')
                net_margin = info.get('profitMargins')
                rev_growth = info.get('revenueGrowth')
                earnings_growth = info.get('earningsGrowth')
                
                gm_p = f"{gross_margin*100:.1f}%" if gross_margin else "N/A"
                om_p = f"{operating_margin*100:.1f}%" if operating_margin else "N/A"
                nm_p = f"{net_margin*100:.1f}%" if net_margin else "N/A"
                
                st.write(f"**שולי רווח גולמי:** {gm_p} | **שולי רווח תפעולי:** {om_p} | **שולי רווח נקי:** {nm_p}")
                
                if rev_growth and rev_growth > 0:
                    st.success(f"✅ צמיחת הכנסות חיובית (רבעונית שנה מול שנה): {rev_growth*100:.1f}%")
                else:
                    st.error(f"❌ אין צמיחת הכנסות או שהצמיחה שלילית: {f'{rev_growth*100:.1f}%' if rev_growth else 'N/A'}")
                    
                if earnings_growth and rev_growth:
                    if earnings_growth > rev_growth:
                        st.success(f"✅ צמיחת ה-EPS בקצב מהיר מההכנסות (מנוף תפעולי חיובי): {earnings_growth*100:.1f}% מול {rev_growth*100:.1f}%")
                    else:
                        st.warning(f"⚠️ צמיחת ה-EPS איטית מקצב צמיחת ההכנסות.")
                
                st.write("---")
                
                # --- 3. דוח מאזן (נזילות ומינוף) ---
                st.subheader("⚖️ דוח מאזן וחוסן פיננסי")
                
                current_ratio = info.get('currentRatio')
                debt_to_equity = info.get('debtToEquity')
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if current_ratio and current_ratio >= 1:
                        st.success(f"✅ יחס שוטף: {current_ratio:.2f} (גדול מ-1, יש נזילות לטווח קצר)")
                    else:
                        st.error(f"❌ יחס שוטף: {current_ratio if current_ratio else 'N/A'} (סיכון נזילות לטווח קצר)")
                        
                with col_b2:
                    if debt_to_equity:
                        leverage = debt_to_equity / 100
                        if leverage <= 1:
                            st.success(f"✅ מנוף פיננסי (חוב להון): {leverage:.2f} (קטן מ-1, רמת מינוף בריאה)")
                        else:
                            st.error(f"❌ מנוף פיננסי (חוב להון): {leverage:.2f} (גדול מ-1, מינוף גבוה)")
                    else:
                        st.write("מידע על מנוף פיננסי אינו זמין")
                        
                st.write("---")
                
                # --- 4. תזרים מזומנים (מנגנון חכם לחברות צמיחה) ---
                st.subheader("💵 ניתוח תזרים מזומנים (מבוסס סקטור)")
                
                try:
                    operating_cash_flow = cashflow.loc['Operating Cash Flow'].iloc[0] if 'Operating Cash Flow' in cashflow.index else info.get('operatingCashflow')
                    capital_expenditure = abs(cashflow.loc['Capital Expenditure'].iloc[0]) if 'Capital Expenditure' in cashflow.index else abs(info.get('capitalExpenditure', 0))
                    free_cash_flow = info.get('freeCashflow')
                    
                    if not free_cash_flow and operating_cash_flow and capital_expenditure:
                        free_cash_flow = operating_cash_flow - capital_expenditure
                except:
                    operating_cash_flow = info.get('operatingCashflow')
                    free_cash_flow = info.get('freeCashflow')
                    capital_expenditure = None

                if operating_cash_flow and free_cash_flow:
                    st.write(f"**תזרים מפעילויות (OCF):** ${operating_cash_flow:,.0f}")
                    st.write(f"**תזרים חופשי (FCF):** ${free_cash_flow:,.0f}")
                    
                    fcf_to_ocf_ratio = free_cash_flow / operating_cash_flow
                    
                    growth_sectors = ['Technology', 'Technology Hardware', 'Semiconductors', 'Energy', 'Clean Energy']
                    is_growth_sector = any(sec.lower() in sector.lower() for sec in growth_sectors)
                    
                    if fcf_to_ocf_ratio >= 0.50:
                        st.success(f"✅ תזרים חופשי מעולה: {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל (יעד: לפחות 50%)")
                    else:
                        if is_growth_sector:
                            st.warning(f"⚠️ תזרים חופשי מהווה {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל. מדובר בחברה בסקטור {sector} - השקעות הוניות גבוהות (CapEx) נפוצות בשלב זה לצורך צמיחה והתרחבות ולכן ה-FCF מכווץ זמנית.")
                        else:
                            st.error(f"❌ תזרים חופשי נמוך: {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל (נמוך מהיעד של חברה יציבה - 50%)")
                            
                    if capital_expenditure:
                        capex_ratio = capital_expenditure / operating_cash_flow
                        st.write(f"**הוצאות הוניות (CapEx) מהתזר:** {capex_ratio*100:.1f}%")
                else:
                    st.info("מידע מלא על תזרים המזומנים אינו זמין בזמן אמת עבור חברה זו.")
                    
            # ==========================================
            # טאב 2: ניתוח טכני (מעודכן ל-3 שנים כברירת מחדל)
            # ==========================================
            with tab2:
                st.header(f"📉 ניתוח טכני וגרף נרות אינטראקטיבי - {ticker}")
                
                # בחירת טווח זמן לגרף - עודכן לגרף 3 שנים כברירת מחדל וסודרו הגרשיים
                period = st.selectbox("בחר טווח זמן לגרף הטכני:", ["3 שנים ('3y')", "שנה ('1y')", "6 חודשים ('6m')", "שנתיים ('2y')"], index=0)
                period_code = "3y" if "3 שנים" in period else "1y" if "שנה" in period else "6m" if "6" in period else "2y"
                
                # משיכת היסטוריית מחירים
                df = stock.history(period=period_code)
                
                if df.empty:
                    st.error("לא ניתן היה למשוך נתוני מחיר היסטוריים לניתוח הטכני.")
                else:
                    # חישוב אינדיקטורים: ממוצעים נעים (SMA 50, SMA 200)
                    df['SMA50'] = df['Close'].rolling(window=50).mean()
                    df['SMA200'] = df['Close'].rolling(window=200).mean()
                    
                    # יצירת גרף נרות יפניים עם Plotly
                    fig = go.Figure()
                    
                    # גרף הנרות
                    fig.add_trace(go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='מחיר מניה'
                    ))
                    
                    # קו ממוצע נע 50
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], mode='lines', name='SMA 50 (טווח קצר-בינוני)', line=dict(color='orange', width=1.5)))
                    
                    # קו ממוצע נע 200
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], mode='lines', name='SMA 200 (טווח ארוך)', line=dict(color='blue', width=1.5)))
                    
                    # עיצוב הגרף
                    fig.update_layout(
                        title=f"גרף נרות יפניים כולל ממוצעים נעים עבור {ticker}",
                        xaxis_title="תאריך",
                        yaxis_title="מחיר בדולר ($)",
                        xaxis_rangeslider_visible=False, # נוחות בטלפון
                        height=600,
                        template="plotly_white"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    last_close = df['Close'].iloc[-1]
                    st.write(f"**מחיר סגירה אחרון:** ${last_close:.2f}")

        except Exception as e:
            st.error(f"אירעה שגיאה בעיבוד הנתונים: {e}")
            st.info("ייתכן שחלק מהנתונים הפיננסיים אינם זמינים כעת ב-Yahoo Finance עבור חברה זו.")

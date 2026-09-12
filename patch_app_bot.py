import codecs

with codecs.open('app.py', 'r', 'utf8') as f:
    app_content = f.read()

injection_code = '''                    except Exception as e:
                        pass
                        
                    try:
                        from src.insider_whale_tracker import LiveInsiderWhaleTracker
                        insider_df = LiveInsiderWhaleTracker.get_live_insider_transactions()
                        if not insider_df.empty:
                            sys_prompt += "\\n\\nLIVE INSIDER TRANSAKTIONEN (SEC Form 4):\\n"
                            sys_prompt += insider_df.to_string(index=False) + "\\n"
                    except Exception as e:
                        pass
'''

app_content = app_content.replace('''                    except Exception as e:
                        pass
                        
                    response = None''', injection_code + '''                        
                    response = None''')

with codecs.open('app.py', 'w', 'utf8') as f:
    f.write(app_content)
print("Patched app.py successfully")

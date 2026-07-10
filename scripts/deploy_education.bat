@echo off
cd /d d:\Cosmic-Lens-Backend
echo STEP2>>deploy_automation.log
git add artifacts/api-server/ask_education artifacts/api-server/openai_helper.py artifacts/api-server/ask_intent_llm.py artifacts/api-server/ask_career/classifier.py artifacts/api-server/ask_career/sector_registry.py artifacts/api-server/scripts/audit_education_full.py artifacts/api-server/tests/test_ask_education_engine.py >>deploy_automation.log 2>&1
echo STEP2 DONE>>deploy_automation.log
git commit -m "Ask: education engine (15 archetypes) + 241-question audit fixes and routing" >>deploy_automation.log 2>&1
echo STEP3 DONE>>deploy_automation.log
git log -1 --oneline >>deploy_automation.log 2>&1
git push >>deploy_automation.log 2>&1
echo STEP4 DONE>>deploy_automation.log
ssh -o BatchMode=yes -o ConnectTimeout=60 root@187.127.174.55 "cd /root/Cosmic-Lens-Backend && find . -name '*.pyc' -delete && git pull && cd artifacts/api-server && pm2 restart cosmic-api --update-env" >>deploy_automation.log 2>&1
echo STEP5 DONE>>deploy_automation.log
echo FINAL DONE>>deploy_automation.log

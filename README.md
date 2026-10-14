# Daily Brief — เว็บอ่านข่าวฟรี

เว็บ HTML แบบ static: ทำงานบน GitHub Pages ฟรี, responsive, หมวดข่าว, บันทึกข่าว, เกม, Dark Mode, ฉบับย้อนหลัง และนำเข้าข้อความจาก ChatGPT ด้วยการวางข้อความ/JSON ได้

## ตั้งค่าโดยไม่ต้องติดตั้งโปรแกรม

1. เข้าสู่ระบบ [GitHub](https://github.com/) สมัครบัญชีฟรีถ้ายังไม่มี
2. สร้าง repository แบบ **Public** ชื่อ `daily-brief` (GitHub Pages แบบ public ใช้งานได้บนแผนฟรี)
3. ในหน้า repository กด **Add file → Upload files**, ลากไฟล์จาก ZIP เข้า repo โดยให้ `index.html`, โฟลเดอร์ `scripts/`, `.github/workflows/`, `data/` อยู่ตำแหน่งตามเดิม (หากอัปโหลดโฟลเดอร์ซ่อน `.github` ยาก ให้ใช้ GitHub เว็บ editor เพิ่มไฟล์ `.github/workflows/daily-news.yml` ตามต้นฉบับ)
4. ไปที่ **Settings → Pages → Build and deployment → Deploy from a branch**, เลือก **GitHub Actions** เป็น Source แล้ว Save
5. ไปที่ **Actions → Daily news refresh and publish → Run workflow** ครั้งแรก (หาก Actions ถูกปิดให้กด Enable)
6. ลองเปิด `https://YOUR_USERNAME.github.io/daily-brief/` เมื่อ GitHub Pages publish เสร็จ โดยเปลี่ยน YOUR_USERNAME เป็นชื่อบัญชีจริง

ระบบตั้งให้เรียก Google News RSS ประมาณ **07:15 น. เวลาไทยทุกวัน** โดย scheduled GitHub Actions อาจเริ่มช้าและไม่ได้มี SLA การทำงานตรงนาทีที่ตั้ง การใช้ Actions ฟรีมี quota/ข้อจำกัดและอาจถูกพักเมื่อ repository ไม่มี activity นาน ๆ หรือมีนโยบายเปลี่ยน ควรตรวจหน้า Actions หากข่าวไม่อัปเดต

## ข้อจำกัดที่ควรทราบ

- RSS ให้พาดหัว/คำอธิบายจากแหล่งข่าว (บางครั้งมีเพียงพาดหัว); **ไม่ใช่บทสรุป AI ของ ChatGPT** และข่าวหลายเรื่องอาจเป็นภาษาต้นทาง
- ไม่สามารถอ่าน Daily Brief ในบทสนทนา ChatGPT/แจ้งเตือนอัตโนมัติโดยตรงได้จากหน้าเว็บนี้ หากต้องการ **ฉบับตรงกัน** ให้คัดลอกข้อความที่ ChatGPT ส่งมาแล้วกด `เพิ่ม Daily Brief` (หรือใช้ JSON รูปแบบตัวอย่าง)
- เนื้อหาที่นำเข้าและข่าวที่ bookmark เก็บใน localStorage ของเบราว์เซอร์เครื่องนั้น **ไม่ sync ข้ามเครื่อง**; ใช้ปุ่ม Export สำรอง JSON ได้ หากต้องการซิงก์ข้ามเครื่องต้องเพิ่มฐานข้อมูลและบัญชีผู้ใช้
- การแก้ไข repository แบบ public ทำให้ไฟล์ที่ commit ขึ้น repo มองเห็นสาธารณะ อย่าใส่ข้อมูลส่วนตัว, API key หรือข้อมูลลับลง repo
- สคริปต์ไม่ต้องใช้ API key และไม่มีค่า OpenAI API; ฟรีภายใต้เงื่อนไข quota ของ GitHub และแหล่ง RSS แต่ไม่มีรับประกัน feed หรือบริการจะใช้งานได้ตลอด

## โครงสร้าง

- `index.html`: หน้าเว็บ
- `scripts/rss_engine.py`: ดึง Google News RSS ด้วย Python standard library
- `scripts/update_news.py`: สร้างไฟล์ข่าว `data/latest.json` และย้อนหลัง
- `.github/workflows/daily-news.yml`: workflow อัปเดตข่าวรายวัน
- `data/archive.json`: รายการวันย้อนหลัง

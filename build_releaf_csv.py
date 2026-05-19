#!/usr/bin/env python3
"""Build a chronological CSV + self-contained HTML app of every Releaf-related
email in Loz's Gmail. Column 1 = direct Gmail URL.

Data sourced from Gmail MCP search_threads results captured in chat.
"""
import csv
import json
from pathlib import Path

GMAIL = "https://mail.google.com/mail/u/0/#all/{}"
HERE = Path(__file__).parent
OUT_CSV = HERE / "releaf_emails_chronology.csv"
OUT_HTML = HERE / "releaf_chronology.html"

# Each tuple: (msg_id, iso_date, sender, to, subject, category, summary)
# Direction is derived from sender (lozturner@* => Outbound).
ROWS = [
    # ───── 2024 ─────
    ("18f2f692b01d85f6", "2024-04-30T14:29:32Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment Loz", "Marketing/Outreach",
     "Graham (registered mental health nurse at Releaf) reaches out after Loz expressed interest in alternative ADHD treatment. First-ever Releaf contact."),
    ("18f957ff61a6d298", "2024-05-20T10:15:40Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Introducing Our New Website!", "Marketing",
     "Announcement of new Releaf website."),
    ("18f95868c3eb386c", "2024-05-20T10:22:53Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Introducing Our New Website!", "Marketing",
     "Duplicate announcement of new Releaf website."),
    ("19002d9738a8c6de", "2024-06-10T15:52:01Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Loz - It's here - the first ever UK grown Medical Cannabis is now available on prescription", "Marketing",
     "Glass Pharms UK-grown cultivar launch announcement."),
    ("19039bcdf2ce7bd0", "2024-06-21T07:39:57Z", "lozturner@gmail.com", "olliekturner@gmail.com",
     "Fwd: Loz - It's here - the first ever UK grown Medical Cannabis is now available on prescription", "Outbound (forward)",
     "Loz forwards the Releaf marketing email to Ollie Turner."),
    ("1907870c8417278b", "2024-07-03T11:52:55Z", "Graham@releaf.co.uk", "lozturner@gmail.com",
     "Loz, the wait is over…", "Marketing/Outreach",
     "Graham again — 'UK-first to all our patients' (Glass Pharms availability)."),
    ("19092f8e12be590b", "2024-07-08T15:31:41Z", "charlene@releaf.co.uk", "lozturner@gmail.com",
     "Loz here's your £50 voucher", "Marketing/Promo",
     "Charlene sends £50 voucher (code 50OFF) for initial consultation."),
    ("1909d3ab6f49ae3b", "2024-07-10T15:19:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Live chat on Jul 10", "Support/Live Chat",
     "Transcript of live chat with Yasemin. Loz mentions he has been delisted from his GP."),
    ("190a1a8771c8397f", "2024-07-11T11:58:07Z", "charlene@releaf.co.uk", "lozturner@gmail.com",
     "⌛Hurry, your £50 voucher expires tomorrow Loz", "Marketing/Promo",
     "Reminder that £50 voucher expires next day."),
    ("19174d1c3cc9ce51", "2024-08-21T12:03:07Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Six Monumental Moments in Six Months of Releaf", "Marketing",
     "Releaf milestone newsletter."),
    ("1922eb2493177f7d", "2024-09-26T14:18:07Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "⌛ Don't Miss Out on £60 Off Your Initial Consultation!", "Marketing/Promo",
     "£60-off initial consultation reminder."),
    ("192d8e6e5e871a4c", "2024-10-29T15:31:03Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "⏱️ £19.99 Consultation (SAVE £79!) Limited Time Offer", "Marketing/Promo",
     "£19.99 initial consultation flash offer."),
    ("1932b26ff7f600be", "2024-11-14T14:49:55Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your reset password link", "Account",
     "Password reset link issued during sign-up."),
    ("1932b3309ef55654", "2024-11-14T14:55:04Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: turner", "Support",
     "Auto-reply acknowledging Loz's first support enquiry (referenced as 'turner')."),
    ("1932bc6f43696d1f", "2024-11-14T17:42:59Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: turner", "Support",
     "Agent confirms ID verification and health questionnaire are complete; awaiting next step."),
    ("1932b34775460730", "2024-11-14T15:02:09Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your initial consultation is booked!", "Appointment Booked",
     "Initial consultation booked — first formal booking on the platform."),
    ("1933006f74d74122", "2024-11-15T13:30:23Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Releaf - Your GP Details", "Clinical/GP",
     "Releaf unable to request Summary of Care — GP (AILSA, 3...) says Loz no longer registered there."),
    ("1934e09da15e9594", "2024-11-21T09:24:48Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your consultation has been amended", "Appointment Amended",
     "Initial consultation rescheduled at patient's request."),
    ("1934e0a4e1e35052", "2024-11-21T09:25:18Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Releaf- Action Required", "Clinical/GP",
     "Releaf asks for correct GP — 'phl adhd' is not a recognised practice in their system."),
    ("1934e0cd9b253964", "2024-11-21T09:23:19Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Releaf- Action Required", "Clinical/GP",
     "Duplicate of the GP details request."),
    ("19363e698cd3027a", "2024-11-25T15:13:37Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Useful Information", "Clinical/GP",
     "Following Loz's call, agent confirms GP details have been updated on Releaf's system."),
    ("1936ed932d216b93", "2024-11-27T18:19:08Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "We need some more information", "Clinical/Info Request",
     "Reviewing Loz's medical info — more information needed before prescription can be issued."),
    ("193815758bfc0b41", "2024-12-01T08:30:02Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 2nd Dec 08:30 initial consultation."),
    ("1938646d276f0c6a", "2024-12-02T07:30:01Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 08:30 consultation."),
    ("193866fed65ef048", "2024-12-02T08:15:01Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("193867d9aef22da5", "2024-12-02T08:29:51Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your reset password link", "Account",
     "Password reset (likely from login attempt around appointment time)."),
    ("1938688c89661119", "2024-12-02T08:42:05Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "We missed you at your appointment today", "Appointment Missed",
     "Loz missed the initial consultation."),
    ("193868c448a0a70a", "2024-12-02T08:45:56Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "We need some more information", "Clinical/Info Request",
     "Repeat request for more medical info."),
    ("193873747eb631b8", "2024-12-02T11:47:38Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your Initial Consultation", "Appointment Missed",
     "Manual support email confirming Loz missed initial consultation and offering rebook slots."),
    ("193da0b9d0cd4e3f", "2024-12-18T13:53:33Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "We need some more information", "Clinical/Info Request",
     "Third info-needed prompt before prescription can be issued."),
    ("193f9657bfb1e1ce", "2024-12-24T15:56:06Z", "support@releaf.co.uk", "hillview.surgery@nhs.net",
     "Releaf- Information Request", "Clinical/GP",
     "Releaf writes to Hillview Surgery (NHS) requesting Loz's medical info; Loz CC'd."),
    ("193f96587f7ac47a", "2024-12-24T15:57:53Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Releaf- Update", "Support",
     "Update on Releaf's progress chasing GP records on Loz's behalf."),
    ("193f9b2532ed497d", "2024-12-24T17:23:53Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: Releaf- Update", "Outbound/Support",
     "Loz replies: 'thank you very much'."),

    # ───── January 2025 ─────
    ("194893fb90a400f3", "2025-01-21T14:24:01Z", "drive-shares-dm-noreply@google.com", "lozturner@gmail.com",
     "Share request for 'LT-Subject Access Request-10-01-2025.pdf'", "Clinical/SAR",
     "Rebekah Goldwater (Releaf) requests access to Loz's Subject Access Request PDF on Drive."),
    ("194894580df1fba5", "2025-01-21T14:23:47Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Item shared with you: 'LT-Subject Access Request-10-01-2025.pdf'", "Clinical/SAR",
     "Auto-reply acknowledging Loz's SAR-related email."),
    ("19498d744a2a6d2b", "2025-01-24T15:03:50Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "We missed you at your appointment today", "Appointment Missed",
     "Another missed consultation."),
    ("19498e3b978af37e", "2025-01-24T15:11:34Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your Initial Consultation", "Appointment Missed",
     "Manual prompt to rebook after missed initial consultation."),
    ("1949d2a477c14548", "2025-01-25T11:13:00Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "We missed you at your appointment today", "Appointment Missed",
     "Yet another missed consultation."),
    ("194a27d5e5660a47", "2025-01-26T11:53:14Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Missed Call", "Support",
     "Support team logs a missed call from Loz."),
    ("194a723f0552e260", "2025-01-27T09:39:15Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your Initial Consultation", "Appointment Missed",
     "Reminder to book another initial consultation after missed appointment."),
    ("194ace5e57f92c74", "2025-01-28T12:28:03Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Subject: Video Appointment at 13:30 Today", "Appointment",
     "Auto-reply / out-of-hours notice."),
    ("194acef57b7ff666", "2025-01-28T12:40:28Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Subject: Video Appointment at 13:30 Today", "Appointment",
     "Agent explains how to join the 13:30 video appointment via patient dashboard."),
    ("194ad40459fdbc80", "2025-01-28T14:10:57Z", "inbox@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "First prescription ready following initial consultation (28 Jan 2025)."),
    ("194b266a4e796549", "2025-01-29T14:10:58Z", "inbox@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is waiting", "Prescription Ready",
     "Reminder prescription is waiting to be ordered."),
    ("194b2381369725f0", "2025-01-29T13:18:34Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Proof of Address", "Clinical/Address",
     "Following a call, agent asks Loz to send proof of address to prevent delivery delays."),
    ("194b79113072ade7", "2025-01-30T14:15:22Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: Proof of Address", "Outbound/Address",
     "Loz responds providing proof of address."),
    ("194b7fd27176fc7b", "2025-01-30T16:06:55Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Proof of Address", "Clinical/Address",
     "Agent confirms address now uploaded — deliveries will go to 5 Nursery Road, Woking GU21 2NN."),

    # ───── February 2025 ─────
    ("194cb22da3ca52c3", "2025-02-03T09:27:18Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your order has been shipped", "Order Shipped",
     "Medical Cannabis Card shop order shipped."),
    ("194cca076a34f23b", "2025-02-03T16:24:01Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Do you want to grant access to your prescription dashboard?", "Account/Card Scan",
     "Loz's Medical Cannabis Card QR code was scanned — prompt to manage access."),
    ("194ccddaef3c885b", "2025-02-03T17:30:40Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Releaf TB-T20 (Tangerine) flower shipped — Loz's first prescription dispatch."),
    ("194ccde9391f5cd2", "2025-02-03T17:32:05Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting parcel, PIN 7253."),
    ("194d040331661dd3", "2025-02-04T09:17:34Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 11:08-12:08", "Delivery/DPD",
     "Out for delivery 4 Feb, driver SANAMPREET, PIN 7253."),
    ("194f55d93320277e", "2025-02-11T14:14:44Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 12 Feb 2025 10:00."),
    ("194f9631d8d1f962", "2025-02-12T09:00:09Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 10:00 follow-up."),
    ("194f98c307128f78", "2025-02-12T09:45:01Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning for 10:00 follow-up."),
    ("194febdb23fd9369", "2025-02-13T09:57:12Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Your FREE Releaf Follow-Up Appointment is Waiting", "Marketing",
     "Free follow-up promo nudge (likely Loz didn't attend the 12 Feb appointment)."),
    ("19503eccd4d688a2", "2025-02-14T10:06:45Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Gift Releaf this Valentine's", "Marketing/Promo",
     "Valentine's referral promo: give £50 / get £50."),
    ("1950429d3d1fcca3", "2025-02-14T11:12:50Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 14 Feb 2025 14:15."),
    ("19504f9bb8721658", "2025-02-14T15:00:18Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Second follow-up booked 14 Mar 2025 10:30 (psychiatrist appt scheduled)."),
    ("1950499315648462", "2025-02-14T13:15:02Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 14:15 appointment on 14 Feb."),
    ("19504df5dbd06a71", "2025-02-14T14:31:41Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready after 14 Feb consultation."),
    ("19504fb1e8ac6e95", "2025-02-14T15:01:59Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your Follow Up Appointment", "Appointment Booked",
     "Manual confirmation: clinician requested follow-up with psychiatrist booked 14 Mar."),
    ("19514c3ef7b87d03", "2025-02-17T16:35:21Z", "noreply@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Releaf MC-T22 (MAC 3) flower shipped."),
    ("19514c54de472c22", "2025-02-17T16:37:09Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting parcel, PIN 9241."),
    ("19518507f78e0294", "2025-02-18T09:08:01Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 13:04-14:04", "Delivery/DPD",
     "Out for delivery 18 Feb, driver SANAMPREET."),

    # ───── March 2025 ─────
    ("195570cb2fbcf7c0", "2025-03-02T13:30:04Z", "invoice+statements+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "New invoice from Releaf #183E0549-65794", "Payment/Invoice",
     "Stripe invoice from Releaf."),
    ("1958f0ddb99cdcc2", "2025-03-13T10:30:00Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 14 Mar 10:30 psychiatrist follow-up."),
    ("19593fd499f866c5", "2025-03-14T09:30:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 10:30 psychiatrist."),
    ("19594267cf3c1822", "2025-03-14T10:15:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("195943f3ae0a78d1", "2025-03-14T10:42:03Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "We missed you at your appointment today", "Appointment Missed",
     "Missed the 14 Mar psychiatrist appointment."),
    ("19594f3836f8f7f1", "2025-03-14T13:59:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your Consultation", "Appointment Missed",
     "Manual nudge: due a follow-up consultation."),
    ("195c7ee8fd89eeab", "2025-03-24T11:33:58Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 25 Mar 19:15."),
    ("195c9948950d03e3", "2025-03-24T19:15:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 25 Mar 19:15."),
    ("195ce83e40e2e5cf", "2025-03-25T18:15:04Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder."),
    ("195ceb92c36d37ba", "2025-03-25T19:00:12Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("195cec824ad12fad", "2025-03-25T19:29:37Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready after 25 Mar consultation."),
    ("195d7e667bd950b3", "2025-03-27T13:59:09Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "SOMAÍ T50 oil 30ml shipped."),
    ("195d7e8da9f5de9f", "2025-03-27T14:01:55Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting parcel, PIN 1426."),
    ("195dc180a779357c", "2025-03-28T09:31:56Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 15:03-16:03", "Delivery/DPD",
     "Out for delivery 28 Mar."),
    ("195e16d50436e2e1", "2025-03-29T10:23:08Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Another prescription ready (a separate item from the 25 Mar treatment plan)."),

    # ───── April 2025 ─────
    ("195fbd6bf52169bd", "2025-04-03T13:28:29Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Releaf GK-T25:C<1 flower shipped."),
    ("195fbd83f354d052", "2025-04-03T13:30:06Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting parcel, PIN 6706."),
    ("195ffdb82e3999f2", "2025-04-04T08:12:10Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 11:20-12:20", "Delivery/DPD",
     "Out for delivery 4 Apr."),
    ("1961eee1976edcef", "2025-04-10T09:00:41Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Your friend saves £50, you earn £50, Loz", "Marketing/Promo",
     "Refer-a-friend campaign."),
    ("1961f09a97e968e5", "2025-04-10T09:30:47Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "SOMAÍ Oils now available again", "Marketing",
     "SOMAÍ oil restocked notification."),
    ("19633bf7467114e9", "2025-04-14T10:01:45Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "🐣Order your medication early for Easter to avoid delays", "Marketing",
     "Easter ordering reminder."),
    ("19634a9f806690ee", "2025-04-14T14:17:53Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 22 Apr 2025 09:00."),
    ("19634aa5a20a3ecc", "2025-04-14T14:18:17Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your consultation has been amended", "Appointment Amended",
     "Amended to 22 Apr 09:15."),
    ("19634aa82f8cf99e", "2025-04-14T14:18:31Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your consultation has been amended", "Appointment Amended",
     "Amended again to 22 Apr 09:00."),
    ("1963dd95fed0ff73", "2025-04-16T09:06:17Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your consultation has been amended", "Appointment Amended",
     "Patient-requested reschedule to 16 Apr 15:00."),
    ("1963eaf6bf1d2ad1", "2025-04-16T13:00:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 16 Apr 15:00."),
    ("1963ed89501079db", "2025-04-16T13:45:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("1963eeb17e88b7af", "2025-04-16T14:05:09Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "We missed you at your appointment today", "Appointment Missed",
     "Missed 16 Apr 15:00 (auto)."),
    ("1963ef4c5657af40", "2025-04-16T14:15:49Z", "lozturner@hotmail.com", "support@releaf.co.uk",
     "No doctor in call", "Outbound/Support",
     "Loz writes (from Hotmail) saying he made the appointment but missed the doctor — implies doctor wasn't in call. (Subsequent delivery delay/bounce errors because he sent from Hotmail address.)"),
    ("1963f20219b1ec27", "2025-04-16T15:03:03Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Rebooked 23 Apr 14:30."),
    ("1963f2234b19f58f", "2025-04-16T15:05:27Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Releaf - Your Appointment", "Support",
     "Agent explains they were expecting Loz for follow-up today; rebooked."),
    ("196446a08d46ead3", "2025-04-17T15:42:02Z", "mailer-daemon@googlemail.com", "lozturner@gmail.com",
     "Delivery Status Notification (Delay)", "Bounce",
     "Loz's 'No doctor in call' email from Hotmail can't deliver."),
    ("1964995b62af1b6f", "2025-04-18T15:47:50Z", "mailer-daemon@googlemail.com", "lozturner@gmail.com",
     "Delivery Status Notification (Delay)", "Bounce",
     "Continuing delivery delay for same Hotmail message."),
    ("1964eba4bcd52b57", "2025-04-19T15:45:53Z", "mailer-daemon@googlemail.com", "lozturner@gmail.com",
     "Delivery Status Notification (Failure)", "Bounce",
     "Final failure — 'Send mail as' settings misconfigured (Hotmail alias)."),
    ("19662a0832e8e06e", "2025-04-23T12:30:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 23 Apr 14:30."),
    ("19662c9a0b035a1d", "2025-04-23T13:15:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("196630e696f2b7dd", "2025-04-23T14:30:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning for follow-on slot at 15:45."),
    ("19662e552a14d74a", "2025-04-23T13:45:07Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 23 Apr 15:45 (likely after the 14:30 slot)."),
    ("196632c03ecd98aa", "2025-04-23T15:02:24Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready after 23 Apr consultation."),
    ("1967c7b5b865e855", "2025-04-28T12:59:37Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Curaleaf T100 oil shipped (Full Spectrum)."),
    ("1967c7cb4badead5", "2025-04-28T13:01:08Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 4205."),
    ("19680b6dd1de23d7", "2025-04-29T08:43:09Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 12:42-13:42", "Delivery/DPD",
     "Out for delivery 29 Apr."),
    ("1968644c457d364d", "2025-04-30T10:36:15Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, Important Update About Your Prescription", "Subscription",
     "Releaf+ — checkout up to 60g per month."),

    # ───── May 2025 ─────
    ("1968be831d17751b", "2025-05-01T12:52:51Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "IMPORTANT: Your Releaf+ Subscription Plan", "Subscription",
     "Releaf+ subscription plan update."),
    ("196aa8d3d5b6717a", "2025-05-07T11:41:39Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been approved", "Prescription Approved",
     "Repeat prescription request approved."),
    ("196b499eb7cea323", "2025-05-09T10:31:37Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Primacann BNB-T26 (Bonne) shipped."),
    ("196b49b2d1f1a471", "2025-05-09T10:33:09Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 1564."),
    ("196b9424336b10d9", "2025-05-10T08:14:08Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 13:48-14:48", "Delivery/DPD",
     "Out for delivery 10 May."),
    ("196dde5bc32a79b9", "2025-05-17T10:58:59Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been approved", "Prescription Approved",
     "Repeat prescription approved (release date 16 May)."),
    ("196ed5502e4de79d", "2025-05-20T10:54:53Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "RE: discount codes for vapourisers", "Marketing/Support",
     "Agent shares discount codes VAPE10 and SK50OFF for Omura vaporisers."),
    ("196ed860cf22a7c9", "2025-05-20T11:48:26Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Pucker Up flower shipped."),
    ("196ed87d55adf7bd", "2025-05-20T11:50:22Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 3889."),
    ("196f1eae27e8d729", "2025-05-21T08:17:03Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 10:03-11:03", "Delivery/DPD",
     "Out for delivery 21 May."),
    ("196fc0c587c3b8d6", "2025-05-23T07:29:49Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been approved", "Prescription Approved",
     "Repeat prescription request approved."),
    ("1970e7ad7e4d1783", "2025-05-26T21:23:39Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 31 May 10:30."),
    ("1971144e2ffd8894", "2025-05-27T10:23:33Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Primacann BNB-T26 (Bonne) shipped."),
    ("19711466485ed8f8", "2025-05-27T10:25:14Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 1373."),
    ("1971591e7900fee7", "2025-05-28T06:26:11Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 10:41-11:41", "Delivery/DPD",
     "Out for delivery 28 May, driver Adrian."),
    ("1971b608c83dc42a", "2025-05-29T09:30:01Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Dr. David Pang @ Sat 31 May 2025 10:30 - 10:40", "Calendar",
     "Google Calendar invite for consultation with Dr David Pang."),
    ("1972086e79bee5ec", "2025-05-30T09:30:00Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 31 May."),
    ("197248c3b428495a", "2025-05-31T04:14:18Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Daily Agenda for Loz Turner as of 5 am", "Calendar",
     "Daily agenda showing the Releaf consultation."),
    ("1972539ee7cbfa9b", "2025-05-31T07:24:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been approved", "Prescription Approved",
     "Repeat prescription approved (release 30 May)."),
    ("1972576520a22e60", "2025-05-31T08:30:00Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for Dr David Pang."),
    ("19725bac84a2e58c", "2025-05-31T09:44:46Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready following Dr Pang consultation."),

    # ───── June 2025 ─────
    ("197351bd3ba492d3", "2025-06-03T09:25:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Releaf GK-T25:C<1 flower shipped."),
    ("197351d815d4c555", "2025-06-03T09:26:54Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 8443."),
    ("1973a0585b981d50", "2025-06-04T08:18:47Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 10:09-11:09", "Delivery/DPD",
     "Out for delivery 4 Jun."),
    ("197a695835297d29", "2025-06-25T10:15:05Z", "support@breethe.com", "lozturner@gmail.com",
     "Is your brain stuck on stress? 😰", "External",
     "Breethe newsletter — surfaced by search because of 'Relief' substring (not Releaf)."),

    # ───── July 2025 ─────
    ("197c7a9f0709afcd", "2025-07-01T20:24:47Z", "msemoneytips@email.moneysavingexpert.com", "lozturner@gmail.com",
     "Cash ISA limit to be slashed?, … free First Direct £200…", "External",
     "MSE newsletter (false-positive: contains 'relief')."),
    ("197e924b6532bdf4", "2025-07-08T08:26:25Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your product request was approved", "Prescription/Approval",
     "Product request for Curaleaf Liquid Vape 420mg THC with Jack Herer approved."),
    ("197ea08a55f9be24", "2025-07-08T12:35:24Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "You're one of 100,000, Loz 🎉", "Marketing",
     "Releaf hits 100,000 patients milestone."),
    ("1980e23259750f6d", "2025-07-15T12:50:40Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "You've authorised a payment to CURVE UK LIMITED", "Payment",
     "£39.99 GBP authorised to Curve (forwarded to Releaf)."),
    ("1980e255e512d0ef", "2025-07-15T12:53:06Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "You've authorised a payment to CURVE UK LIMITED", "Payment",
     "£234.97 GBP authorised to Curve."),
    ("1980e2891bc40fe8", "2025-07-15T12:56:35Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Subject: Urgent Inquiry Regarding Prescription Change for Laurence Turner", "Outbound/Support",
     "Loz asks about vape order — last month told a battery would be included to make it functional."),
    ("1980e293a42f1b24", "2025-07-15T12:57:18Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Thank You For Contacting Releaf", "Support",
     "Auto-acknowledgement of vape/battery enquiry."),
    ("1980e356b5bcc009", "2025-07-15T13:10:37Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "PLEASE CONFIRM ADDRESS:", "Outbound/Address",
     "Urgent — Loz warns NOT to ship to old billing address 10 Burriton House; recently changed."),
    ("1980e3411eed070e", "2025-07-15T13:11:25Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Thank You For Contacting Releaf", "Support",
     "Auto-acknowledgement of address email."),
    ("198122c220eda605", "2025-07-16T07:38:58Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: PLEASE CONFIRM ADDRESS:", "Clinical/Address",
     "Natalie confirms delivery address: 5 Nursery Road, Woking GU21 2NN."),
    ("19812442e80b7445", "2025-07-16T08:05:13Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Thank You For Contacting Releaf", "Support",
     "Harvey confirms battery is included with first vape order; future orders are cartridge only."),
    ("198125c53369405d", "2025-07-16T08:31:35Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: PLEASE CONFIRM ADDRESS:", "Outbound/Address",
     "Loz double-checks 5 Nursery Road is the delivery address (not billing)."),
    ("198125cd30856d38", "2025-07-16T08:32:08Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: PLEASE CONFIRM ADDRESS:", "Outbound/Support",
     "Loz also asks whether vape comes with the battery."),
    ("19812b98876c37cb", "2025-07-16T10:13:23Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: PLEASE CONFIRM ADDRESS:", "Outbound/Support",
     "Loz asks them to halt delivery if vape doesn't include the battery — limited disability budget."),
    ("19812ca649ad6559", "2025-07-16T10:31:49Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: Thank You For Contacting Releaf", "Outbound/Support",
     "Loz apologises for jumping the gun — saw the confirmation about the battery."),
    ("19812d12dad680a3", "2025-07-16T10:39:13Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 9192."),
    ("19812d139e3eb555", "2025-07-16T10:39:17Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Lemonatti flower shipped."),
    ("1981774a5e503517", "2025-07-17T08:16:15Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 10:23-11:23", "Delivery/DPD",
     "Out for delivery 17 Jul, driver SANAMPREET."),
    ("1981e526a19bda75", "2025-07-18T16:16:12Z", "creator-spotlight@mail.beehiiv.com", "lozturner@gmail.com",
     "🔴 $6M, 39 states: A new monetization framework", "External",
     "Creator newsletter (false-positive: 'relief' in body)."),
    ("19812ee4fd653be1", "2025-07-16T07:16:00Z", "patients@levaclinic.com", "lozturner@gmail.com",
     "Introducing Leva Wellness 🌿 Relief beyond prescriptions", "External/Competitor",
     "Leva Clinic competitor pitching CBD wellness products."),
    ("1982fab41ba9e050", "2025-07-22T01:06:48Z", "mailer@upworthy.com", "lozturner@gmail.com",
     "Woman praises Target for taking responsibility after a pet toy killed her cat", "External",
     "Upworthy newsletter (false-positive)."),
    ("1983783d072e4c29", "2025-07-23T13:43:18Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "(no subject)", "Outbound/Support",
     "Empty/short email to Releaf support."),
    ("1983786b755b2fb2", "2025-07-23T13:43:50Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Thank You For Contacting Releaf", "Support",
     "Auto-acknowledgement."),
    ("1983c1f57515b1c9", "2025-07-24T11:08:59Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: (no subject)", "Support",
     "Rebecca asks what Loz needs help with."),
    ("198461e7f742e6a1", "2025-07-26T09:44:20Z", "patients@levaclinic.com", "lozturner@gmail.com",
     "Introducing Leva Wellness 🌿 Relief beyond prescriptions", "External/Competitor",
     "Leva Clinic competitor pitch (repeat)."),
    ("198520a7ffdd9548", "2025-07-28T17:17:54Z", "marketing@releaf.co.uk", "lozturner@gmail.com",
     "Easier Strain Selection & More Monthly Flexibility", "Marketing",
     "Product update — more strain flexibility."),
    ("1985ff94e95c70e8", "2025-07-31T10:13:50Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: (no subject)", "Outbound/Support",
     "Loz asks about the new vape cartridge — wants clarification on use."),
    ("1986022cb7e1ec62", "2025-07-31T10:59:05Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: (no subject)", "Support",
     "Rebecca advises keeping the cartridge upright so liquid pools at the bottom."),
    ("198605f1c236c74f", "2025-07-31T12:04:59Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: (no subject)", "Outbound/Support",
     "Loz unsatisfied — was told a technical team would respond; asks for escalation."),
    ("198618bc348ca377", "2025-07-31T17:30:03Z", "patientsupport@curaleafclinic.com", "lozturner@gmail.com",
     "Curaleaf Clinic - July Update", "External",
     "Curaleaf Clinic newsletter."),

    # ───── August 2025 ─────
    ("19865d4c24842795", "2025-08-01T13:31:37Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Planning a Trip? Releaf Travel Certificates", "Marketing",
     "Promo: travel certificates via patient dashboard."),
    ("19866e28ae0fc5aa", "2025-08-01T18:26:19Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "You've authorised a payment to CURVE UK LIMITED", "Payment",
     "£79.99 GBP via Curve (Releaf subscription/order)."),
    ("1986c5347a350960", "2025-08-02T19:47:33Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 14 Aug 15:30."),
    ("19874487d0fba605", "2025-08-04T08:52:43Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your order has been shipped", "Order Shipped",
     "Shop order shipped — Releaf Battery for Vape Cartridges."),
    ("19875466602f613f", "2025-08-04T13:30:03Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Releaf", "Support",
     "Agent thanks Loz for phone call; asks him to reply with photos for the resolutions team."),
    ("198757d4a8eb51e9", "2025-08-04T14:30:01Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Dr. Michal Modestowicz @ Thu 14 Aug 2025 15:30", "Calendar",
     "Google Calendar invite for Dr Michal Modestowicz consultation."),
    ("1987a2582f2371b0", "2025-08-05T12:12:13Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 7180."),
    ("1987a2584d3414e2", "2025-08-05T12:10:12Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Strawberry Cake flower shipped."),
    ("1987df716e74fd87", "2025-08-06T06:00:00Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 08:48-09:48", "Delivery/DPD",
     "Out for delivery 6 Aug."),
    ("1987ec06b38aa0d5", "2025-08-06T09:39:55Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your request to change your delivery date to Thursday 7th Aug", "Delivery/DPD",
     "DPD reschedules delivery to 7 Aug at Loz's request."),
    ("1987ef6bce746c12", "2025-08-06T10:39:15Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready following recent consultation."),
    ("1988315e7aa8ee49", "2025-08-07T05:51:47Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 09:09-10:09", "Delivery/DPD",
     "Out for delivery 7 Aug."),
    ("19884f02fe4b7240", "2025-08-07T14:29:49Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Dr. Michal Modestowicz @ Thu 14 Aug 2025 15:30", "Calendar",
     "Calendar reminder for upcoming Dr Modestowicz consultation."),
    ("19888acd15db5d5e", "2025-08-08T07:54:43Z", "notifications@reclaim.ai", "lozturner@gmail.com",
     "🎉 Weekly Report at Reclaim: Aug 2 - 8", "External",
     "Reclaim weekly report (false-positive)."),
    ("19898fb3801befb3", "2025-08-11T11:54:16Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Curaleaf Liquid Vape 420mg THC Jack Herer shipped."),
    ("19898ff64f0d5d7b", "2025-08-11T11:58:51Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 7775."),
    ("1989cfc7a038c255", "2025-08-12T06:34:07Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 15:16-16:16", "Delivery/DPD",
     "Out for delivery 12 Aug."),
    ("1989eb001a58a70a", "2025-08-12T14:29:50Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Dr. Michal Modestowicz @ Thu 14 Aug 2025 15:30", "Calendar",
     "Calendar reminder."),
    ("198a3d6903380c87", "2025-08-13T14:30:03Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for Dr Modestowicz 14 Aug 15:30."),
    ("198a78caa8f300f5", "2025-08-14T07:47:50Z", "trevor@trevorlabs.com", "lozturner@gmail.com",
     "Good morning, Loz! Here's today's action plan...", "External",
     "Trevor Labs morning plan (false-positive: mentions Releaf in agenda)."),
    ("198a8c60a6192521", "2025-08-14T13:30:05Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 15:30 Dr Modestowicz."),
    ("198a8ef577aab70d", "2025-08-14T14:15:10Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("198a9373345117b1", "2025-08-14T15:33:42Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 14 Aug 16:45 (immediately rebooked from earlier slot)."),
    ("198cc1b73a5fc6b2", "2025-08-21T10:10:07Z", "resolutions@releaf.co.uk", "lozturner@gmail.com",
     "Releaf: Consultation", "Support/Resolutions",
     "Resolutions team rebooks Loz for 27 Aug 15:00 after he missed an appointment with Dr Imran."),
    ("198e6ae032834cc9", "2025-08-26T14:00:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 27 Aug 15:00."),
    ("198eb9d5f107a470", "2025-08-27T13:00:04Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder."),
    ("198ebc66e87a283f", "2025-08-27T13:45:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("198ebd54ac8721de", "2025-08-27T14:01:19Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "💬 Share your insights for 20% off", "Marketing",
     "Patient survey invite — 20% off shop."),
    ("198f0581aca51f91", "2025-08-28T11:02:42Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "woops.. there was an issue with your code", "Marketing",
     "Patient survey discount code can now be redeemed."),
    ("19900a82c42f3b70", "2025-08-31T15:04:05Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "💬 Weekend Check-in", "Marketing",
     "Treatment-plan weekend check-in nudge."),

    # ───── September 2025 ─────
    ("1992dcf94676dfb8", "2025-09-09T09:30:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 10 Sep 10:30."),
    ("1992ee270185b4c1", "2025-09-09T14:30:14Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "💬 Last chance to get 20% off shop", "Marketing",
     "Patient survey last chance."),
    ("19932bf1c7854269", "2025-09-10T08:30:09Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder."),
    ("19932e82e16fefc3", "2025-09-10T09:15:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("199338247309f313", "2025-09-10T12:03:18Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready after 10 Sep consultation."),
    ("1994e2a0c575c8f2", "2025-09-15T16:16:41Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "📲 Introducing Flexible Payments with Klarna", "Marketing",
     "Klarna payment integration announcement."),
    ("1998637943118f39", "2025-09-26T13:30:11Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "⏰ Get 10% off CBD Products for a limited time", "Marketing",
     "10% off CBD promo."),

    # ───── October 2025 ─────
    ("199a020eee664297", "2025-10-01T14:15:36Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "where is my order please", "Outbound/Support",
     "Loz chases an undispatched order; attaches live-chat transcript."),
    ("199a021a4b84d468", "2025-10-01T14:16:22Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Thank You For Contacting Releaf", "Support",
     "Auto-acknowledgement."),
    ("199a44606def09ea", "2025-10-02T09:34:36Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: where is my order please", "Support",
     "Agent apologises for the delay; can't explain the reason; escalating."),
    ("199a529ee8d16b1a", "2025-10-02T13:43:32Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: where is my order please", "Outbound/Support",
     "Loz says he's satisfied a second consultation reactivated his script; needs an ETA on delivery."),
    ("199a5970a1e83cb2", "2025-10-02T15:42:42Z", "invoice+statements+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "Your refund from Releaf #3202-8689", "Payment/Refund",
     "Refund issued from Releaf via Stripe."),
    ("199b94e1713c0669", "2025-10-06T11:35:26Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Acai Berry flower shipped."),
    ("199b94f9f32edced", "2025-10-06T11:37:06Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 2012."),
    ("199b962ac8dac981", "2025-10-06T11:57:55Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: where is my order please", "Outbound/Support",
     "Loz follows up — no reply from Emily despite urgent flag; phoned support too."),
    ("199b997a8ee5ebf2", "2025-10-06T12:55:47Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: where is my order please", "Outbound/Support",
     "Loz notes that 15 mins after his chase, the order was suddenly dispatched."),
    ("199bdb6e1c38eacf", "2025-10-07T08:08:21Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 13:13-14:13", "Delivery/DPD",
     "Out for delivery 7 Oct."),
    ("199bde7aff86dcd5", "2025-10-07T09:01:39Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "🔥 Releaf+ Upgrade: Extra Benefits Available Now!", "Marketing/Subscription",
     "Releaf+ subscription upgrade promo."),
    ("199c4647db50f83c", "2025-10-08T15:15:42Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "RE: Your Releaf+ Subscription", "Subscription",
     "Survey: tell us how we can improve subscription experience."),
    ("199e01640021e2fc", "2025-10-14T00:19:37Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "You've authorised a payment to CURVE UK LIMITED", "Payment",
     "£79.99 GBP via Curve."),
    ("199e20ad2db5d941", "2025-10-14T09:26:23Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Voiceflow Conversation - 68ed9586bde7164978f68309", "Support/Live Chat",
     "After live chat with bot Lily, agent confirms some requested products are in stock."),
    ("199e7400abf02111", "2025-10-15T09:42:37Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Ultra Sour flower shipped."),
    ("199e741778b149ae", "2025-10-15T09:44:09Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 9388."),
    ("19a0a055e1d1902d", "2025-10-22T03:45:13Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "You've authorised a payment to CURVE UK LIMITED", "Payment",
     "£79.99 GBP via Curve."),
    ("19a1017a2b81e641", "2025-10-23T08:02:55Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "It's time to book your follow-up", "Appointment Reminder",
     "Nudge to book follow-up before next prescription."),
    ("19a10a928e293a07", "2025-10-23T10:41:52Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Platinum Garlic flower shipped."),
    ("19a10abb9e9e0743", "2025-10-23T10:44:39Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary Ltd parcel", "Delivery/DPD",
     "DPD expecting, PIN 4530."),
    ("19a14d03ce221943", "2025-10-24T06:03:02Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 12:03-13:03", "Delivery/DPD",
     "Out for delivery 24 Oct, driver Adrian."),
    ("19a2b202e608ef55", "2025-10-28T14:02:00Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£154.98 payment to Releaf was unsuccessful", "Payment Failed",
     "Stripe could not charge card — first attempt."),
    ("19a2b2087e0dc192", "2025-10-28T14:02:23Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£154.98 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe retry failed."),
    ("19a2b20ea0d8a9ea", "2025-10-28T14:02:48Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£154.98 payment to Releaf was unsuccessful again", "Payment Failed",
     "Another Stripe retry failed."),
    ("19a30ed0a0bdd385", "2025-10-29T17:03:52Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Updates to our Patient Terms", "Policy",
     "Releaf updates Patient Terms clarifying chargeback/dispute policy."),
    ("19a39869a10eeb9e", "2025-10-31T09:08:33Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£154.98 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe retry failed."),
    ("19a3986f5c984edb", "2025-10-31T09:08:56Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Strawberry Cake — prescription paid (likely via PayPal/Curve)."),
    ("19a398765b944593", "2025-10-31T09:09:24Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "CURVE UK LIMITED: £154.98 GBP", "Payment",
     "£154.98 authorised via Curve (covering the Stripe failure)."),

    # ───── November 2025 ─────
    ("19a3ea62445e908f", "2025-11-01T09:01:07Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "7 years of medical cannabis in the UK 💚", "Marketing",
     "Anniversary newsletter + patient survey results."),
    ("19a4f312a285439b", "2025-11-04T14:06:53Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Strawberry Cake flower shipped."),
    ("19a531f7fefb56bf", "2025-11-05T08:26:02Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary Ltd order will be delivered today between 12:50-13:50", "Delivery/DPD",
     "Out for delivery 5 Nov, driver Nuradin."),
    ("19a6fc43c8ca4b6f", "2025-11-10T21:55:22Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "Releaf GP-T21 (Grape Kush) — prescription paid."),
    ("19a6fc4b3fd98043", "2025-11-10T21:55:52Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "CURVE UK LIMITED: £159.98 GBP", "Payment",
     "£159.98 authorised via Curve."),
    ("19a6fc609b931a10", "2025-11-10T21:57:20Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 19 Nov 10:30 with Rachel McCusker."),
    ("19a7814b055de5ae", "2025-11-12T12:40:12Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 8525."),
    ("19a7891c4df22164", "2025-11-12T14:56:49Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Releaf GP-T21 (Grape Kush) flower shipped."),
    ("19a7c7490b95f752", "2025-11-13T09:03:25Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf parcel will be delivered today between 13:56 - 14:56", "Delivery/DPD",
     "Out for delivery 13 Nov, driver Fuad."),
    ("19a915d7f2e0f355", "2025-11-17T10:30:14Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Rachel McCusker @ Wed 19 Nov 2025 10:30 - 10:40", "Calendar",
     "Calendar invite for Rachel McCusker 19 Nov 10:30."),
    ("19a9683ccda4deb9", "2025-11-18T10:30:10Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 19 Nov 10:30."),
    ("19a97b37403f7097", "2025-11-18T16:01:50Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Login issues cause by Global Cloudflare outages", "Service Outage",
     "Releaf advises global Cloudflare outage is affecting login."),
    ("19a9b7320bf54344", "2025-11-19T09:30:04Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder."),
    ("19a9b9c488b09cf1", "2025-11-19T10:15:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("19a9bb3679db5a8b", "2025-11-19T10:40:16Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready after 19 Nov consultation with Rachel McCusker."),
    ("19a9ca7b289d859e", "2025-11-19T15:07:07Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "RE; Support", "Support/Complaint",
     "Releaf (Emily) reaches out about Loz's dissatisfaction — wants to resolve."),
    ("19a9d26c5a060b06", "2025-11-19T17:25:54Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: RE; Support", "Outbound/Complaint",
     "Loz says he can send the whole previous email thread; mentions partial refund after re-initial that was odd."),
    ("19aa15b9ad8ffe29", "2025-11-20T13:02:05Z", "LGO@public.govdelivery.com", "lozturner@gmail.com",
     "New adult social care complaint decisions", "External",
     "Local Government Ombudsman newsletter (false-positive)."),
    ("19aa65e8d40e0e2b", "2025-11-21T12:23:25Z", "lozturner@gmail.com", "lozturner+perplexity@gmail.com",
     "Inbox Progress Log: Friday, November 21, 2025", "Personal Note",
     "Loz's own inbox progress log — mentions Releaf among many other items."),
    ("19aa76a3a32b3ec0", "2025-11-21T17:15:47Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Exclusive Offers this Self Care Week 🧘", "Marketing",
     "Self Care Week R+ promo."),
    ("19ab6b53f89bcdb8", "2025-11-24T16:32:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: RE; Support", "Support/Complaint",
     "Emily Creighton confirms colleague Liberty processed Loz's refund on 06/10."),
    ("19ab80a122e3d321", "2025-11-24T22:44:19Z", "lozturner@gmail.com", "tasia835@gmail.com",
     "Fwd: RE; Support", "Outbound/Forward",
     "Loz forwards Emily's refund-confirmation reply to advocate Tasia."),
    ("19aba226465c6a4a", "2025-11-25T08:30:06Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Invitation: priority access to £80 savings", "Marketing",
     "Promo: £80 off / £19.99 consultation invite."),
    ("19ac95fdb63351d7", "2025-11-28T07:31:32Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "💚 Exclusive: 15% off shop", "Marketing",
     "15% off shop until Monday."),

    # ───── December 2025 ─────
    ("19ad8ba029c3a389", "2025-12-01T07:04:19Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Releaf+ rewards: Exclusive boosted discounts 💸", "Marketing/Subscription",
     "Releaf+ rewards email."),
    ("19ad976d1831fe3a", "2025-12-01T10:30:32Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Ends today: £80 off your Initial Consultation", "Marketing",
     "£19.99 consultation last-chance."),
    ("19afd7fd0007d999", "2025-12-08T10:26:42Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 18 Dec 14:45."),
    ("19afe6c8ef844536", "2025-12-08T14:45:17Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Emma Hopkins @ Thu 18 Dec 2025 14:45", "Calendar",
     "Calendar invite for Emma Hopkins consultation."),
    ("19b01455ade0e961", "2025-12-09T04:01:20Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Hollywood flower — prescription paid."),
    ("19b07f7642553e7e", "2025-12-10T11:13:30Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 3530."),
    ("19b081a54d3b31da", "2025-12-10T11:51:41Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Hollywood flower shipped."),
    ("19b0c89e2b81046b", "2025-12-11T08:32:01Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf order will be delivered today between 14:05 - 15:05", "Delivery/DPD",
     "Out for delivery 11 Dec."),
    ("19b0d9b2c0d66781", "2025-12-11T13:30:31Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Important: Holiday pharmacy hours 🎄", "Notice",
     "Christmas/New Year pharmacy hours."),
    ("19b0ddf824b77bff", "2025-12-11T14:45:10Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Emma Hopkins @ Thu 18 Dec 2025 14:45", "Calendar",
     "Calendar reminder."),
    ("19b11c610ef8efc9", "2025-12-12T08:55:51Z", "notifications@reclaim.ai", "lozturner@gmail.com",
     "🎉 Weekly Report at Reclaim: Dec 6 - 12", "External",
     "Reclaim newsletter (false-positive)."),
    ("19b11d7ca1352e3f", "2025-12-12T09:15:11Z", "noreply.invitations@trustpilotmail.com", "lozturner@gmail.com",
     "How was your experience with Releaf?", "Review Request",
     "Trustpilot review invitation."),
    ("19b279f0051e19c4", "2025-12-16T14:44:50Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Emma Hopkins @ Thu 18 Dec 2025 14:45", "Calendar",
     "Calendar reminder."),
    ("19b28bcce0ff2f89", "2025-12-16T19:57:00Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "6 days left to order medication 🎄", "Notice",
     "Festive ordering deadline reminder."),
    ("19b29483974a3f5d", "2025-12-16T22:29:17Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe charge failed."),
    ("19b2948bd90b9662", "2025-12-16T22:29:51Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Repeat failure."),
    ("19b2948fe8f56c58", "2025-12-16T22:30:08Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Repeat failure."),
    ("19b29b2d52aac909", "2025-12-17T00:25:43Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Repeat failure."),
    ("19b2a31803752f97", "2025-12-17T02:44:05Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Repeat failure."),
    ("19b2cc58d7c7006b", "2025-12-17T14:45:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 18 Dec 14:45."),
    ("19b2e5189b76c482", "2025-12-17T21:57:33Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Repeat failure."),
    ("19b2e521e7f3b262", "2025-12-17T21:58:11Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Repeat failure."),
    ("19b2e524b5018399", "2025-12-17T21:58:23Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Repeat failure."),
    ("19b2e59ba2fd4b7c", "2025-12-17T22:06:30Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Moby Dick 10g — prescription paid (after retries cleared)."),
    ("19b2ffd1e6f6a193", "2025-12-18T05:44:35Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Daily Agenda for Loz Turner as of 5 am", "Calendar",
     "Daily agenda includes Releaf consultation."),
    ("19b31b4f9af26c9c", "2025-12-18T13:45:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 18 Dec 14:45 Emma Hopkins."),
    ("19b31de2da699b1c", "2025-12-18T14:30:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("19b3219a5cd9ce63", "2025-12-18T15:35:01Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "Re: 15 minutes until your appointment", "Outbound/Complaint",
     "Loz reports significant technical issues during 14:45 consultation — couldn't connect properly."),
    ("19b321a54a4c0cb3", "2025-12-18T15:35:43Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Thank you for contacting Releaf", "Support",
     "Auto-acknowledgement."),
    ("19b35e4c1d6e9c3f", "2025-12-19T09:15:40Z", "noreply.invitations@trustpilotmail.com", "lozturner@gmail.com",
     "How was your experience with Releaf?", "Review Request",
     "Trustpilot invite."),
    ("19b365511d62f256", "2025-12-19T11:18:22Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: 15 minutes until your appointment", "Appointment Rebooked",
     "Rebekah confirms rebook to 21 Dec 08:30."),
    ("19b3654152887eb4", "2025-12-19T11:17:15Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Follow-up booked 21 Dec 08:30."),
    ("19b396f46f9bb47f", "2025-12-20T01:45:52Z", "lozturner@gmail.com", "support+privacy@wisprflow.ai",
     "GDPR Data Export Request", "External/Outbound",
     "GDPR SAR sent to Wispr (not Releaf) — appeared in this search through thread continuation."),
    ("19b3976e17447c98", "2025-12-20T01:54:09Z", "wispr@service.usepylon.com", "lozturner@gmail.com",
     "Re: GDPR Data Export Request", "External",
     "Wispr support auto-reply."),
    ("19b39770a7cfa5c7", "2025-12-20T01:54:20Z", "wispr@service.usepylon.com", "lozturner@gmail.com",
     "Re: GDPR Data Export Request", "External",
     "Wispr routes to human agent."),
    ("19b3ac97e7e4438d", "2025-12-20T08:04:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your monthly allowance has been renewed", "Allowance Renewed",
     "Monthly allowance renewed: 30g flower + 0.5ml vape cartridge."),
    ("19b3ad55a83837ef", "2025-12-20T08:16:57Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your consultation has been cancelled", "Appointment Cancelled",
     "21 Dec 08:30 consultation cancelled."),
    ("19b3aed59d48ce18", "2025-12-20T08:43:11Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your follow-up consultation is booked", "Appointment Booked",
     "Rebooked to 3 Jan 2026 07:30."),
    ("19b3ae9973426d8c", "2025-12-20T08:39:05Z", "lozturner@gmail.com", "support@releaf.co.uk",
     "15 minutes until your appointment", "Outbound/Complaint",
     "Loz: appointment was moved again without notification — has screenshots; needs explanation."),
    ("19b454f89c0c759a", "2025-12-22T09:06:38Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 5859."),
    ("19b46770bc6c68e2", "2025-12-22T14:29:24Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: 15 minutes until your appointment", "Support/Complaint",
     "Agent apologises for confusion; confirms a colleague called on 20 Dec to discuss the change."),
    ("19b472de6b9771e4", "2025-12-22T17:49:08Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Moby Dick flower shipped."),
    ("19b4763653ee2175", "2025-12-22T18:47:34Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Coming soon: Releaf Protect", "Marketing/Subscription",
     "Releaf Protect (R+ exclusive) preview."),
    ("19b47e791423e90a", "2025-12-22T21:11:56Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Lucy In The Sky — prescription paid."),
    ("19b4a7aa0fee8dc2", "2025-12-23T09:11:49Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf parcel will be delivered today between 10:09 - 11:09", "Delivery/DPD",
     "Out for delivery 23 Dec, driver Daniel."),
    ("19b4b1ffdcc9c185", "2025-12-23T12:12:25Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 4836."),
    ("19b4c233dfb6ce8d", "2025-12-23T16:55:34Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Lucy In The Sky flower shipped."),
    ("19b4f43d14e840b9", "2025-12-24T07:30:02Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Dr. Haroon Hamid @ Sat 3 Jan 2026 07:30", "Calendar",
     "Calendar invite for Dr Haroon Hamid 3 Jan 07:30."),
    ("19b4f6e16e1ffe7e", "2025-12-24T08:16:12Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf parcel will be delivered today between 13:17 - 14:17", "Delivery/DPD",
     "Out for delivery 24 Dec, driver Simbarashe."),
    ("19b50d410ccb12b9", "2025-12-24T14:47:13Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£119.98 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19b50fde22ba84ce", "2025-12-24T15:32:54Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "Curaleaf T10:C10 Mixed Berries pastilles — prescription paid."),
    ("19b514e97b4de084", "2025-12-24T17:01:03Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your Holiday Card from Releaf 💚", "Marketing",
     "Christmas card from Releaf."),
    ("19b573932e57bdf9", "2025-12-25T20:35:24Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful", "Payment Failed",
     "Stripe failure."),
    ("19b59e380ccedb99", "2025-12-26T09:00:39Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Enjoy 10% Off the Releaf Shop 🎄", "Marketing",
     "10% off shop festive promo."),
    ("19b5eb6dc21ceefb", "2025-12-27T07:30:00Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Dr. Haroon Hamid @ Sat 3 Jan 2026 07:30", "Calendar",
     "Calendar reminder."),
    ("19b69c232e4fb5b7", "2025-12-29T10:58:13Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 4707."),
    ("19b6b1fb5265ac46", "2025-12-29T17:19:58Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Curaleaf T10:C10 Mixed Berries shipped."),
    ("19b6e91baf0fe209", "2025-12-30T09:23:22Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf parcel will be delivered today between 14:49 - 15:49", "Delivery/DPD",
     "Out for delivery 30 Dec, driver Yadeta."),
    ("19b7242a41090f11", "2025-12-31T02:35:28Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure (Releaf+ subscription)."),

    # ───── January 2026 ─────
    ("19b78767f7b05534", "2026-01-01T07:29:49Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Dr. Haroon Hamid @ Sat 3 Jan 2026 07:30", "Calendar",
     "Calendar reminder."),
    ("19b7d9d0d86de904", "2026-01-02T07:30:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your appointment is in 24 hours", "Appointment Reminder",
     "24-hour reminder for 3 Jan 07:30 (later subject of formal complaint)."),
    ("19b804bd6b08bdf9", "2026-01-02T20:00:12Z", "wispr@service.usepylon.com", "lozturner@gmail.com",
     "Re: GDPR Data Export Request", "External",
     "Wispr returns SAR data (unrelated to Releaf — same thread)."),
    ("19b825953fff33ea", "2026-01-03T05:34:10Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Daily Agenda for Loz Turner as of 5 am", "Calendar",
     "Daily agenda includes the Releaf consultation."),
    ("19b828c75168be32", "2026-01-03T06:30:00Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Loz, your appointment is today", "Appointment Today",
     "Day-of reminder for 3 Jan 07:30 with Dr Haroon Hamid."),
    ("19b82b5ab79f03a8", "2026-01-03T07:15:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "15 minutes until your appointment", "Appointment Imminent",
     "15-minute warning."),
    ("19b82cd391eb18ec", "2026-01-03T07:40:45Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription is ready to order", "Prescription Ready",
     "Prescription ready after 3 Jan consultation (later disputed in formal complaint)."),
    ("19b866e43957d529", "2026-01-04T00:35:31Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe Releaf+ subscription retry failed."),
    ("19b9cf61a25f016d", "2026-01-08T09:35:32Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19bac6948cf66e3c", "2026-01-11T09:35:39Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19baf863a9d7722e", "2026-01-12T00:06:08Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£124.97 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19bc2a153a9eae89", "2026-01-15T17:08:29Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Lucy In The Sky — prescription paid."),
    ("19bc2ba3956260d4", "2026-01-15T17:35:42Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Subscription retry failed."),
    ("19bc7586a6b76bfd", "2026-01-16T15:06:54Z", "lozturner@gmail.com", "lozturner@gmail.com",
     "DRAFT 1 - Relief Subscription Payment Made in Error - Refund Required", "Complaint Draft",
     "Loz drafts formal complaint demanding refund of subscription payment made in error; mentions advocate Natasha."),
    ("19bc759a86c583bc", "2026-01-16T15:08:19Z", "lozturner@gmail.com", "lozturner@gmail.com",
     "DRAFT 2 - Formal Complaint: Consultation Notes Not Reflecting What Was Agreed & Approved", "Complaint Draft",
     "Loz drafts formal complaint about 3 Jan consultation notes — pattern of errors affecting care."),
    ("19bd075ea657ae14", "2026-01-18T09:35:47Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Subscription retry failed."),
    ("19bd66ffabfe4551", "2026-01-19T13:27:01Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Live chat query from Loz", "Support/Live Chat",
     "Auto-confirmation of live chat enquiry."),
    ("19be4e87ccb4e182", "2026-01-22T08:53:18Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Live chat query from Loz", "Support/Live Chat",
     "Confirms parcel delivered 20 Jan."),
    ("19bda6ee1437df61", "2026-01-20T08:04:17Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your monthly allowance has been renewed", "Allowance Renewed",
     "Monthly allowance renewed: 60ml oil / 60g flower / 0.5ml vape."),
    ("19bdaf025e047d05", "2026-01-20T10:25:29Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 2460."),
    ("19bdbe352d95bb17", "2026-01-20T14:51:05Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Lucy In The Sky flower shipped."),
    ("19bdfd494ef239a0", "2026-01-21T09:13:28Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf order will be delivered today between 13:09 - 14:09", "Delivery/DPD",
     "Out for delivery 21 Jan, driver Simbarashe."),
    ("19bdfe8f511876e5", "2026-01-21T09:35:44Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Subscription retry failed."),
    ("19be0dd94bdadecd", "2026-01-21T14:02:56Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your order from Releaf", "Delivery/DPD",
     "DPD missed Loz — delivery options offered."),
    ("19be76b94ccb6764", "2026-01-22T20:35:45Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Subscription retry failed."),

    # ───── February 2026 ─────
    ("19c4de5143aca167", "2026-02-11T18:09:43Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Correct GP Details", "Clinical/GP",
     "GP notification letter returned — note says Loz no longer registered."),
    ("19c7a145c6ba2237", "2026-02-20T08:04:40Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your monthly allowance has been renewed", "Allowance Renewed",
     "Monthly allowance renewed: 60ml oil / 60g flower / 2ml vape."),
    ("19c8b07f3e6f543d", "2026-02-23T15:04:39Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Correct GP Details", "Clinical/GP",
     "Follow-up — no GP update received yet; want to avoid prescription delays."),

    # ───── March 2026 ─────
    ("19cc08c0b9520b65", "2026-03-06T00:28:48Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Subscription retry failed."),
    ("19cc08e1922211e9", "2026-03-06T00:31:03Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£39.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Subscription retry failed."),
    ("19cc0bf2e26188f3", "2026-03-06T01:24:39Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "PayPal Debit Card purchase at RELEAF."),
    ("19cc0c1064c2308d", "2026-03-06T01:26:39Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "Second PayPal Debit Card purchase at RELEAF."),
    ("19cc0c22a3b1e8a0", "2026-03-06T01:27:55Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "Third PayPal Debit Card purchase at RELEAF."),
    ("19cc0c0d700d3b07", "2026-03-06T01:26:29Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Afghan Lights 10g — prescription paid."),
    ("19cc0c20b6496219", "2026-03-06T01:27:47Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "Kallie Lazer Fuel 10g — prescription paid."),
    ("19cc7f00fcb3ac3f", "2026-03-07T10:55:23Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 9677."),
    ("19cc84c9f2d8361f", "2026-03-07T12:36:30Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "Kallie Lazer Fuel flower shipped."),
    ("19cd29b75a4c6f2c", "2026-03-09T12:38:48Z", "support@wispr.ai", "lozturner@gmail.com",
     "Flow Support Request", "External",
     "Unrelated Wispr Flow support thread (false-positive)."),
    ("19cd29e34268e090", "2026-03-09T12:41:49Z", "support@wispr.ai", "support@wispr.ai",
     "Re: Flow Support Request", "External",
     "Wispr support."),
    ("19cd2e14c256b1a1", "2026-03-09T13:55:05Z", "lozturner@gmail.com", "support@wispr.ai",
     "Re: Flow Support Request", "External/Outbound",
     "Loz asserts GDPR rights to data export (Wispr, not Releaf)."),
    ("19cd2e24c7585a9b", "2026-03-09T13:56:11Z", "support@wispr.ai", "lozturner@gmail.com",
     "Re: Flow Support Request", "External",
     "Wispr brings in another agent."),
    ("19cd2e268ae6a169", "2026-03-09T13:56:17Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting, PIN 1050."),
    ("19cd37c8b1d56dff", "2026-03-09T16:44:38Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Afghan Lights flower shipped."),
    ("19cd74cb2249c6f9", "2026-03-10T10:30:52Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "Sorry, your Releaf parcel is delayed due to an unexpected issue", "Delivery/DPD",
     "DPD delays parcel."),
    ("19cd77f4f72e747a", "2026-03-10T11:26:09Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 14:20 - 15:20", "Delivery/DPD",
     "Out for delivery 10 Mar, driver KALEB."),
    ("19cdaa6578974cae", "2026-03-11T02:07:39Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs CLV 85/1 vape cartridge Cherry — prescription paid."),
    ("19cdaa9c56e945b9", "2026-03-11T02:11:24Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Afghan Lights 20g — prescription paid."),
    ("19cdaa67b2d30809", "2026-03-11T02:07:49Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "PayPal Debit Card purchase at RELEAF."),
    ("19cdaa9edcfd6d8e", "2026-03-11T02:11:34Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "PayPal Debit Card purchase at RELEAF."),
    ("19cdaa7d1eb9d065", "2026-03-11T02:09:16Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£159.98 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19cdaa8aa2fa17ea", "2026-03-11T02:10:12Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£159.98 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19cdaa92554741d6", "2026-03-11T02:10:43Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£159.98 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19cdc18b7a2d23da", "2026-03-11T08:52:11Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf parcel will be delivered today between 11:16 - 12:16", "Delivery/DPD",
     "Out for delivery 11 Mar, driver Abass Suleiman."),
    ("19cdc5725a14d7de", "2026-03-11T10:00:23Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "🚭 No Smoking Day: 15% off vaporisers", "Marketing",
     "Vaporiser promo (No Smoking Day)."),
    ("19ce16eca5fee841", "2026-03-12T09:44:18Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf parcel", "Delivery/DPD",
     "DPD expecting, PIN 4357."),
    ("19ce1776ccd32cca", "2026-03-12T09:53:45Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting, PIN 9160."),
    ("19ce237314a56a40", "2026-03-12T13:23:13Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs CLV 85/1 vape cartridge shipped."),
    ("19ce23dde94cda3a", "2026-03-12T13:30:30Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Afghan Lights flower shipped."),
    ("19ce6646e83cf647", "2026-03-13T08:51:05Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 13:09 - 14:09", "Delivery/DPD",
     "Out for delivery 13 Mar, driver Ali."),
    ("19ce66468517baf2", "2026-03-13T08:51:05Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf order will be delivered today between 13:08 - 14:08", "Delivery/DPD",
     "Out for delivery 13 Mar (second parcel)."),
    ("19ce6a471893a4ec", "2026-03-13T10:01:00Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Important update on your prescription deliveries 🚚", "Notice",
     "Releaf adds a second pharmacy partner."),
    ("19cebcaf19ff1600", "2026-03-14T10:01:10Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "It's time to book your follow-up", "Appointment Reminder",
     "Nudge to book follow-up to review treatment plan."),
    ("19d022dfe2a2d216", "2026-03-18T18:21:01Z", "support@wispr.ai", "lozturner@gmail.com",
     "Re: Flow Support Request", "External",
     "Wispr export confirmation (false-positive thread)."),
    ("19d10c04e5b9dd52", "2026-03-21T14:15:31Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19d19b9608b35619", "2026-03-23T08:04:20Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your monthly allowance has been renewed", "Allowance Renewed",
     "Monthly allowance renewed: 60ml oil / 60g flower / 2ml vape."),
    ("19d2a04cb4a3ce36", "2026-03-26T12:00:49Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "An update on Easter deliveries 🚚", "Notice",
     "Easter bank holiday pharmacy closures."),
    ("19d3a8b6a4d49e7e", "2026-03-29T17:01:48Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Afghan Lights 10g — prescription paid."),
    ("19d3e288f89e5c7e", "2026-03-30T09:52:17Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting, PIN 7318."),
    ("19d42d34ae2f57c2", "2026-03-31T07:37:16Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Afghan Lights flower shipped."),

    # ───── April 2026 ─────
    ("19d4821988d5e053", "2026-04-01T08:20:53Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 12:09 - 13:09", "Delivery/DPD",
     "Out for delivery 1 Apr, driver Abass Suleiman."),
    ("19d4e2405fd73d83", "2026-04-02T12:21:16Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Strawberry Cake 10g — prescription paid."),
    ("19d4fa6e0299299a", "2026-04-02T19:23:49Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Citroli 10g — prescription paid."),
    ("19d4e24277434a3c", "2026-04-02T12:21:25Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "PayPal Debit Card purchase at RELEAF."),
    ("19d4fa710671b8e4", "2026-04-02T19:23:59Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "Second PayPal Debit Card purchase at RELEAF."),
    ("19d4f3f7b855bda2", "2026-04-02T17:30:52Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "New month, new Releaf+ rewards", "Marketing/Subscription",
     "Monthly R+ rewards email."),
    ("19d609cdc31695b7", "2026-04-06T02:26:25Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "PayPal Debit Card purchase at RELEAF (£39.99 subscription)."),
    ("19d6385e021e46a9", "2026-04-06T16:00:03Z", "lozturner@gmail.com", "lozturner@gmail.com",
     "ACTION REQUIRED: RELEAF £39.99 charge - Build Subscription Tracking System NOW (Los Multiverse Spreadsheet)", "Personal Note",
     "Loz notes another £39.99 RELEAF charge — wake-up call to build subscription tracker."),
    ("19d638c30aa8b4d2", "2026-04-06T16:07:04Z", "lozturner@gmail.com", "lozturner@gmail.com",
     "WRAP-UP SUMMARY: Subscription Tracker System - Everything Done, Here's What's Live", "Personal Note",
     "Loz documents the tracker system created in response to the RELEAF charge."),
    ("19d66c3e28881be5", "2026-04-07T07:06:44Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting, PIN 3401."),
    ("19d671ad2bded5ca", "2026-04-07T08:41:44Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting (second parcel), PIN 0742."),
    ("19d686d520b94d82", "2026-04-07T14:51:28Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Strawberry Cake flower shipped."),
    ("19d688513ecd0a08", "2026-04-07T15:17:24Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Citroli 10g shipped."),
    ("19d6c27446c4cf2a", "2026-04-08T08:13:24Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 14:08 - 15:08", "Delivery/DPD",
     "Out for delivery 8 Apr, driver Abass Suleiman."),
    ("19d6c2749d9bffb5", "2026-04-08T08:13:25Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 14:08 - 15:08", "Delivery/DPD",
     "Duplicate DPD notification (second parcel)."),
    ("19d72db39ab0fe0d", "2026-04-09T15:27:42Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Wedding Cake Crash — prescription paid."),
    ("19d72e8380ebdb06", "2026-04-09T15:41:54Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19d8693e68a8a7f5", "2026-04-13T11:22:13Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting, PIN 5375."),
    ("19d8ca9fecf805e1", "2026-04-14T15:44:04Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Wedding Cake Crash flower shipped."),
    ("19d9037b4ac7db08", "2026-04-15T08:17:42Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 13:07 - 14:07", "Delivery/DPD",
     "Out for delivery 15 Apr, driver Nuradin."),
    ("19db95eaadf0b1fa", "2026-04-23T08:04:41Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your monthly allowance has been renewed", "Allowance Renewed",
     "Monthly allowance renewed: 60ml oil / 60g flower / 2ml vape."),
    ("19dd52e658299ac2", "2026-04-28T17:41:20Z", "failed-payments+acct_1KxtVAG6Q3OdnJYH@stripe.com", "lozturner@gmail.com",
     "£79.99 payment to Releaf was unsuccessful again", "Payment Failed",
     "Stripe failure."),
    ("19dd52e997395da8", "2026-04-28T17:41:33Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs D. Burger 10g — prescription paid."),
    ("19dd52ed29772ebe", "2026-04-28T17:41:48Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "PayPal Debit Card purchase at RELEAF."),
    ("19dd5467abde5810", "2026-04-28T18:07:39Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "Subsequent PayPal Debit Card purchase at KNAPHILL NEWS (same card)."),
    ("19dd8b5e275ff44f", "2026-04-29T10:08:11Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting, PIN 0456."),
    ("19dd9e1219fb178d", "2026-04-29T15:35:02Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs D. Burger flower shipped."),
    ("19ddd02422e21511", "2026-04-30T06:10:05Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 10:07 - 11:07", "Delivery/DPD",
     "Out for delivery 30 Apr, driver Ali."),

    # ───── May 2026 ─────
    ("19de0dc97e6c36d5", "2026-05-01T00:07:25Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been paid", "Prescription Paid",
     "4C Labs Afghan Lights 10g — prescription paid."),
    ("19de0dcb1d4326e2", "2026-05-01T00:07:32Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "PayPal Debit Card purchase at RELEAF."),
    ("19de269f27d35011", "2026-05-01T07:21:27Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "Unrelated PayPal receipt at Your Local Store (same card; surfaced via thread)."),
    ("19de3f21c0948831", "2026-05-01T14:29:46Z", "service@paypal.co.uk", "lozturner@gmail.com",
     "Receipt for your PayPal Debit Card purchase", "Payment",
     "Unrelated PayPal receipt at Morrisons Daily (same card; thread)."),
    ("19de35e5bf5cbb8f", "2026-05-01T11:48:23Z", "yourorder@dpd.co.uk", "lozturner@gmail.com",
     "We're expecting your Releaf Dispensary parcel", "Delivery/DPD",
     "DPD expecting, PIN 2424."),
    ("19de40bc113ae1fa", "2026-05-01T14:57:48Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your prescription has been shipped", "Prescription Shipped",
     "4C Labs Afghan Lights flower shipped."),
    ("19de7c1263158619", "2026-05-02T08:14:47Z", "yourdelivery@dpd.co.uk", "lozturner@gmail.com",
     "Your Releaf Dispensary order will be delivered today between 10:24 - 11:24", "Delivery/DPD",
     "Out for delivery 2 May, driver Galin (EV)."),
    ("19e1b342efe3860e", "2026-05-12T08:00:52Z", "info@bignarstiemedical.com", "lozturner@gmail.com",
     "Re: New customer message on 11 May 2026 at 14:20", "External/Switch",
     "Big Narstie Medical (competitor clinic) — asks Loz to complete eligibility form."),
    ("19e1bc827239f7e6", "2026-05-12T10:42:42Z", "lozturner@gmail.com", "info@bignarstiemedical.com",
     "Re: New customer message on 11 May 2026 at 14:20", "Outbound/Switch",
     "Loz confirms eligibility form complete; asks about moving over from Releaf."),
    ("19e1bcade9f114b0", "2026-05-12T10:45:29Z", "info@bignarstiemedical.com", "lozturner@gmail.com",
     "Re: New customer message on 11 May 2026 at 14:20", "External/Switch",
     "BNM asks for ID, proof of address, and brief summary of care."),
    ("19e1bd01111b9915", "2026-05-12T10:51:20Z", "lozturner@gmail.com", "info@bignarstiemedical.com",
     "Re: New customer message on 11 May 2026 at 14:20", "Outbound/Switch",
     "Loz uploads documents."),
    ("19e1bd3a29a6a1b7", "2026-05-12T10:54:59Z", "info@bignarstiemedical.com", "lozturner@gmail.com",
     "Re: New customer message on 11 May 2026 at 14:20", "External/Switch",
     "BNM clarifies what a Brief Summary of Care must include."),
    ("19e227ca5e6bb495", "2026-05-13T17:57:33Z", "dr.sue.clenton@releaf.co.uk", "lozturner@gmail.com",
     "Exciting news about your follow-up care", "Marketing/Clinical",
     "Dr Sue Clenton announces changes to follow-up care."),
    ("19e2538fdc6f7dc4", "2026-05-14T06:42:31Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "You need to book a consultation to continue with your reorder", "Appointment Reminder",
     "Health questionnaire flagged a next step — consultation required before reorder."),
    ("19e2b9c35c2c3f3e", "2026-05-15T12:28:37Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Thank you for contacting Releaf", "Support",
     "Auto-acknowledgement (Loz's outbound message not shown in search — likely a contact form submission)."),
    ("19e38fcfa532e8a6", "2026-05-18T02:49:23Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your consultation has been amended", "Appointment Amended",
     "Amended to 22 May 2026 07:30."),
    ("19e3aa4a22944a5c", "2026-05-18T10:32:08Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your Concern Has Been Escalated", "Support/Escalation",
     "Resolutions team picks up Loz's complaint."),
    ("19e3b02d58848147", "2026-05-18T12:15:00Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Re: Contact Form Message from Laurence Turrner", "Support/Refund",
     "Agent confirms a 20% refund of £30.99 has been processed; tried to call Loz."),
    ("19e4009416eb78ff", "2026-05-19T11:40:07Z", "sue@releaf.co.uk", "lozturner@gmail.com",
     "RE: more options for your next follow-up 👇", "Marketing/Clinical",
     "Sue pitches the 3-minute follow-up option (no doctor required)."),
    ("19e401d583254f98", "2026-05-19T12:02:05Z", "support@releaf.co.uk", "lozturner@gmail.com",
     "Your consultation has been amended", "Appointment Amended",
     "Amended to 21 May 2026 13:45."),
    ("19e40446e3d7052b", "2026-05-19T12:44:46Z", "calendar-notification@google.com", "lozturner@gmail.com",
     "Notification: Releaf Video Consultation - Renae Carney @ Thu 21 May 2026 13:45 - 13:55", "Calendar",
     "Calendar invite for Renae Carney consultation on 21 May 2026."),
]

ROWS.sort(key=lambda r: r[1])

def direction(sender: str) -> str:
    return "Outbound" if sender.lower().startswith("lozturner@") else "Inbound"

HEADERS = [
    "Gmail URL", "Date (UTC)", "From", "To", "Direction",
    "Subject", "Category", "Summary of what happened",
]

# ─── CSV ────────────────────────────────────────────────────────────────────
with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_ALL)
    w.writerow(HEADERS)
    for msg_id, date, sender, to, subject, category, summary in ROWS:
        w.writerow([
            GMAIL.format(msg_id), date, sender, to, direction(sender),
            subject, category, summary,
        ])
print(f"Wrote {len(ROWS)} rows to {OUT_CSV}")

# ─── HTML (single self-contained file with embedded JSON DB + multi-page UI)
records = [
    {
        "id": msg_id,
        "url": GMAIL.format(msg_id),
        "date": date,
        "from": sender,
        "to": to,
        "direction": direction(sender),
        "subject": subject,
        "category": category,
        "summary": summary,
    }
    for (msg_id, date, sender, to, subject, category, summary) in ROWS
]
DATA_JSON = json.dumps(records, ensure_ascii=False)

HTML = """<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Releaf — Email Chronology</title>
<style>
:root {
  --bg: #f4f4f1; --pane: #ffffff; --text: #111827; --muted: #6b7280;
  --border: #e5e7eb; --border-soft: #f1f5f9;
  --accent: #0f766e; --accent-soft: #ccfbf1; --accent-text: #134e4a;
  --star: #f59e0b; --star-soft: #fef3c7;
  --warn: #b91c1c; --warn-soft: #fee2e2;
  --ok: #166534; --ok-soft: #dcfce7;
  --purple: #6d28d9; --purple-soft: #ede9fe;
  --shadow: 0 1px 2px rgba(0,0,0,.04), 0 1px 3px rgba(0,0,0,.06);
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, \"Segoe UI\", Helvetica, Arial, sans-serif; }
header { background: var(--card); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 50;
  padding: 12px 20px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
header h1 { margin: 0 16px 0 0; font-size: 18px; }
header nav button { background: transparent; border: 1px solid transparent; padding: 6px 12px;
  border-radius: 6px; cursor: pointer; font: inherit; color: var(--muted); }
header nav button.active { background: var(--accent); color: white; }
header nav button:hover:not(.active) { background: var(--accent-soft); color: var(--accent); }
header .meta { margin-left: auto; color: var(--muted); font-size: 12px; }
main { padding: 20px; max-width: 1400px; margin: 0 auto; }
.page { display: none; }
.page.active { display: block; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 16px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap: 12px; }
.stat { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
.stat .n { font-size: 26px; font-weight: 600; }
.stat .l { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .05em; }
.cat-bar { display: flex; flex-direction: column; gap: 4px; margin-top: 8px; }
.cat-row { display: grid; grid-template-columns: 1fr 50px; gap: 6px; align-items: center; }
.cat-name { font-size: 12px; color: var(--muted); }
.cat-bar-fill { background: var(--accent-soft); border-radius: 4px; height: 14px; position: relative; }
.cat-bar-fill > span { background: var(--accent); border-radius: 4px; height: 100%; display: block; }
.cat-count { text-align: right; font-size: 12px; color: var(--muted); }

.controls { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
.controls input, .controls select { padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; font: inherit; }
.controls input[type=search] { min-width: 240px; }
button.btn { padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border); background: white; cursor: pointer; }
button.btn:hover { background: #f1f5f9; }

table.tbl { width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; font-size: 13px; }
table.tbl thead { background: #f1f5f9; }
table.tbl th { text-align: left; padding: 8px 10px; font-weight: 600; font-size: 12px; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; }
table.tbl th.sorted::after { content: \" \\25BE\"; }
table.tbl th.sorted.asc::after { content: \" \\25B4\"; }
table.tbl td { padding: 8px 10px; vertical-align: top; border-bottom: 1px solid var(--border); }
table.tbl tr:last-child td { border-bottom: none; }
table.tbl tr:hover { background: #f8fafc; }
.subject { font-weight: 500; }
.summary { color: var(--muted); }
.tag { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; background: var(--accent-soft); color: var(--accent); white-space: nowrap; }
.tag.warn { background: var(--warn-soft); color: var(--warn); }
.tag.ok { background: var(--ok-soft); color: var(--ok); }
.tag.muted { background: #f1f5f9; color: var(--muted); }
.dir { font-size: 11px; padding: 2px 6px; border-radius: 4px; }
.dir.Inbound { background: #ede9fe; color: #5b21b6; }
.dir.Outbound { background: #fef3c7; color: #92400e; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.gmail-link { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; }

textarea.note { width: 100%; min-height: 36px; padding: 6px; border: 1px dashed var(--border); border-radius: 6px; font: inherit; background: #fffbe7; resize: vertical; }
textarea.note:focus { outline: 2px solid var(--accent); border-style: solid; background: white; }

.timeline { position: relative; padding-left: 18px; }
.timeline::before { content: \"\"; position: absolute; left: 5px; top: 0; bottom: 0; width: 2px; background: var(--border); }
.tl-month { font-weight: 600; margin: 16px 0 6px -18px; padding-left: 18px; color: var(--muted); position: sticky; top: 60px; background: var(--bg); padding-top: 4px; padding-bottom: 4px; z-index: 1; }
.tl-item { position: relative; margin-bottom: 10px; padding: 8px 12px; background: var(--card); border: 1px solid var(--border); border-radius: 8px; }
.tl-item::before { content: \"\"; position: absolute; left: -16px; top: 14px; width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
.tl-item .h { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.tl-item .h .when { color: var(--muted); font-size: 12px; }
.tl-item .summary { margin-top: 4px; font-size: 13px; }

.muted { color: var(--muted); }
.small { font-size: 12px; }

@media (max-width: 720px) {
  .col-from, .col-to, .col-direction { display: none; }
  header h1 { font-size: 16px; }
}
</style>
</head>
<body>
<header>
  <h1>Releaf Chronology</h1>
  <nav id=\"tabs\">
    <button data-tab=\"overview\" class=\"active\">Overview</button>
    <button data-tab=\"timeline\">Timeline</button>
    <button data-tab=\"table\">Spreadsheet</button>
    <button data-tab=\"notes\">My Notes</button>
  </nav>
  <div class=\"meta\" id=\"metaCount\"></div>
</header>
<main>
  <section id=\"page-overview\" class=\"page active\"></section>
  <section id=\"page-timeline\" class=\"page\"></section>
  <section id=\"page-table\" class=\"page\"></section>
  <section id=\"page-notes\" class=\"page\"></section>
</main>

<script>
const DATA = __DATA_JSON__;
const LS_KEY = \"releafNotes_v1\";

// ─── Note persistence (per Gmail message id) ───
function loadNotes() { try { return JSON.parse(localStorage.getItem(LS_KEY) || \"{}\"); } catch(e) { return {}; } }
function saveNotes(n) { localStorage.setItem(LS_KEY, JSON.stringify(n)); }
let notes = loadNotes();
function setNote(id, val) { if (val) notes[id] = val; else delete notes[id]; saveNotes(notes); renderNotesPage(); }

// ─── Tab routing ───
document.getElementById(\"tabs\").addEventListener(\"click\", (e) => {
  const btn = e.target.closest(\"button[data-tab]\"); if (!btn) return;
  for (const b of document.querySelectorAll(\"#tabs button\")) b.classList.toggle(\"active\", b === btn);
  for (const p of document.querySelectorAll(\".page\")) p.classList.toggle(\"active\", p.id === \"page-\" + btn.dataset.tab);
  if (btn.dataset.tab === \"notes\") renderNotesPage();
  window.scrollTo(0,0);
});

// ─── Helpers ───
function fmtDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString(\"en-GB\", { dateStyle: \"medium\", timeStyle: \"short\" });
}
function fmtMonth(iso) {
  return new Date(iso).toLocaleString(\"en-GB\", { year: \"numeric\", month: \"long\" });
}
function categoryClass(cat) {
  if (/fail|bounce|complaint|missed|cancelled/i.test(cat)) return \"tag warn\";
  if (/shipped|paid|approved|booked|delivered/i.test(cat)) return \"tag ok\";
  if (/marketing|calendar|external/i.test(cat)) return \"tag muted\";
  return \"tag\";
}
function esc(s) { return String(s).replace(/[&<>\\\"']/g, c => ({\"&\":\"&amp;\",\"<\":\"&lt;\",\">\":\"&gt;\",\"\\\"\":\"&quot;\",\"'\":\"&#39;\"}[c])); }

document.getElementById(\"metaCount\").textContent = DATA.length + \" emails • \" + fmtMonth(DATA[0].date) + \" → \" + fmtMonth(DATA[DATA.length-1].date);

// ─── Overview ───
function renderOverview() {
  const byCat = {}; const byDir = {Inbound:0, Outbound:0};
  let firstDate = DATA[0].date, lastDate = DATA[0].date;
  for (const r of DATA) {
    byCat[r.category] = (byCat[r.category]||0) + 1;
    byDir[r.direction] = (byDir[r.direction]||0) + 1;
    if (r.date < firstDate) firstDate = r.date;
    if (r.date > lastDate) lastDate = r.date;
  }
  const cats = Object.entries(byCat).sort((a,b)=>b[1]-a[1]);
  const maxN = cats[0][1];

  const headlines = [
    { n: DATA.length, l: \"Total emails\" },
    { n: byDir.Inbound, l: \"Inbound\" },
    { n: byDir.Outbound, l: \"Outbound from you\" },
    { n: Object.keys(byCat).length, l: \"Distinct categories\" },
  ];

  document.getElementById(\"page-overview\").innerHTML = `
    <div class=\"card\">
      <h2 style=\"margin-top:0\">Releaf relationship at a glance</h2>
      <p class=\"muted\">Every email captured between you and Releaf (medical cannabis clinic) and the surrounding systems — DPD deliveries, Stripe payments, PayPal/Curve receipts, calendar invites — from <strong>${fmtDate(firstDate)}</strong> to <strong>${fmtDate(lastDate)}</strong>. Click any row in the Spreadsheet tab to jump straight to that email in Gmail.</p>
    </div>
    <div class=\"stats\">${headlines.map(h => `<div class=\"stat\"><div class=\"n\">${h.n}</div><div class=\"l\">${esc(h.l)}</div></div>`).join(\"\")}</div>
    <div class=\"card\">
      <h3 style=\"margin-top:0\">Emails by category</h3>
      <div class=\"cat-bar\">
        ${cats.map(([name, n]) => `
          <div class=\"cat-row\">
            <div>
              <div class=\"cat-name\">${esc(name)}</div>
              <div class=\"cat-bar-fill\"><span style=\"width:${(n/maxN)*100}%\"></span></div>
            </div>
            <div class=\"cat-count\">${n}</div>
          </div>`).join(\"\")}
      </div>
    </div>
    <div class=\"card\">
      <h3 style=\"margin-top:0\">Key flashpoints</h3>
      <ul>
        <li><strong>Nov 2024 – Dec 2024:</strong> GP registration problems (AILSA / phl adhd not recognised), multiple missed initial consultations, repeated requests for medical info.</li>
        <li><strong>Jan – Feb 2025:</strong> Proof-of-address required after the move; first prescriptions begin shipping (TB-T20 flower, etc).</li>
        <li><strong>July 2025:</strong> Vape battery confusion; urgent address-confirmation thread; you ask them to halt delivery.</li>
        <li><strong>Oct 2025:</strong> Order undispatched — you chase, refund issued via Stripe (#3202-8689); Emily eventually confirms Liberty processed it.</li>
        <li><strong>Dec 2025:</strong> Tech-failed consultation on 18 Dec, appointment moved without notice — drafted complaints (DRAFT 1 & 2).</li>
        <li><strong>Jan 2026:</strong> Formal complaint about 3 Jan consultation notes; subscription payment dispute; ongoing Stripe failures.</li>
        <li><strong>Feb 2026:</strong> GP letter returned again — \"no longer registered\".</li>
        <li><strong>May 2026:</strong> You're exploring Big Narstie Medical as an alternative; Releaf escalates your concern and issues 20% refund (£30.99). New consultation 21 May with Renae Carney.</li>
      </ul>
    </div>
  `;
}

// ─── Timeline ───
function renderTimeline() {
  const root = document.getElementById(\"page-timeline\");
  let html = `<div class=\"controls\">
    <input id=\"tlSearch\" type=\"search\" placeholder=\"Search subject or summary…\">
    <select id=\"tlCat\"><option value=\"\">All categories</option></select>
    <span class=\"muted small\" id=\"tlCount\"></span>
  </div><div class=\"timeline\" id=\"tlBody\"></div>`;
  root.innerHTML = html;

  const cats = [...new Set(DATA.map(r => r.category))].sort();
  const sel = root.querySelector(\"#tlCat\");
  for (const c of cats) { const o = document.createElement(\"option\"); o.value = c; o.textContent = c; sel.appendChild(o); }

  function draw() {
    const q = root.querySelector(\"#tlSearch\").value.toLowerCase();
    const cat = sel.value;
    const filtered = DATA.filter(r =>
      (!cat || r.category === cat) &&
      (!q || (r.subject + \" \" + r.summary + \" \" + r.from).toLowerCase().includes(q))
    );
    root.querySelector(\"#tlCount\").textContent = filtered.length + \" of \" + DATA.length;
    const body = root.querySelector(\"#tlBody\");
    let out = \"\"; let lastMonth = \"\";
    for (const r of filtered) {
      const m = fmtMonth(r.date);
      if (m !== lastMonth) { out += `<div class=\"tl-month\">${esc(m)}</div>`; lastMonth = m; }
      out += `<div class=\"tl-item\">
        <div class=\"h\">
          <span class=\"when\">${fmtDate(r.date)}</span>
          <span class=\"dir ${r.direction}\">${r.direction}</span>
          <span class=\"${categoryClass(r.category)}\">${esc(r.category)}</span>
          <a href=\"${r.url}\" target=\"_blank\" rel=\"noopener\" class=\"gmail-link\">↗ open</a>
        </div>
        <div class=\"subject\">${esc(r.subject)}</div>
        <div class=\"muted small\">${esc(r.from)} → ${esc(r.to)}</div>
        <div class=\"summary\">${esc(r.summary)}</div>
        ${notes[r.id] ? `<div class=\"muted small\" style=\"margin-top:4px;color:#92400e\">📝 ${esc(notes[r.id])}</div>` : \"\"}
      </div>`;
    }
    body.innerHTML = out || \"<p class='muted'>No matches.</p>\";
  }
  root.querySelector(\"#tlSearch\").addEventListener(\"input\", draw);
  sel.addEventListener(\"change\", draw);
  draw();
}

// ─── Spreadsheet ───
let sortKey = \"date\", sortAsc = true;
function renderTable() {
  const root = document.getElementById(\"page-table\");
  root.innerHTML = `<div class=\"controls\">
    <input id=\"tblSearch\" type=\"search\" placeholder=\"Search anything…\">
    <select id=\"tblCat\"><option value=\"\">All categories</option></select>
    <select id=\"tblDir\"><option value=\"\">All directions</option><option>Inbound</option><option>Outbound</option></select>
    <button class=\"btn\" id=\"exportNotes\">Export my notes (JSON)</button>
    <button class=\"btn\" id=\"clearFilters\">Reset</button>
    <span class=\"muted small\" id=\"tblCount\"></span>
  </div>
  <div style=\"overflow-x:auto\">
    <table class=\"tbl\">
      <thead><tr>
        <th data-k=\"url\">Gmail</th>
        <th data-k=\"date\" class=\"sorted asc\">Date</th>
        <th data-k=\"from\" class=\"col-from\">From</th>
        <th data-k=\"to\" class=\"col-to\">To</th>
        <th data-k=\"direction\" class=\"col-direction\">Dir</th>
        <th data-k=\"subject\">Subject</th>
        <th data-k=\"category\">Category</th>
        <th>Summary</th>
        <th>Notes</th>
      </tr></thead>
      <tbody id=\"tblBody\"></tbody>
    </table>
  </div>`;

  const cats = [...new Set(DATA.map(r => r.category))].sort();
  const sel = root.querySelector(\"#tblCat\");
  for (const c of cats) { const o = document.createElement(\"option\"); o.value = c; o.textContent = c; sel.appendChild(o); }

  function draw() {
    const q = root.querySelector(\"#tblSearch\").value.toLowerCase();
    const cat = sel.value;
    const dir = root.querySelector(\"#tblDir\").value;
    const filtered = DATA.filter(r =>
      (!cat || r.category === cat) &&
      (!dir || r.direction === dir) &&
      (!q || (r.subject + \" \" + r.summary + \" \" + r.from + \" \" + r.to + \" \" + r.category).toLowerCase().includes(q))
    );
    filtered.sort((a, b) => {
      const av = (a[sortKey] || \"\").toString();
      const bv = (b[sortKey] || \"\").toString();
      return (sortAsc ? 1 : -1) * av.localeCompare(bv);
    });
    root.querySelector(\"#tblCount\").textContent = filtered.length + \" of \" + DATA.length;
    const body = root.querySelector(\"#tblBody\");
    body.innerHTML = filtered.map(r => `
      <tr>
        <td><a href=\"${r.url}\" target=\"_blank\" rel=\"noopener\" class=\"gmail-link\" title=\"Open in Gmail\">↗ ${esc(r.id.slice(0,8))}</a></td>
        <td class=\"small\">${fmtDate(r.date)}</td>
        <td class=\"col-from small\">${esc(r.from)}</td>
        <td class=\"col-to small\">${esc(r.to)}</td>
        <td class=\"col-direction\"><span class=\"dir ${r.direction}\">${r.direction}</span></td>
        <td class=\"subject\">${esc(r.subject)}</td>
        <td><span class=\"${categoryClass(r.category)}\">${esc(r.category)}</span></td>
        <td class=\"summary\">${esc(r.summary)}</td>
        <td><textarea class=\"note\" data-id=\"${r.id}\" placeholder=\"Add note…\">${esc(notes[r.id] || \"\")}</textarea></td>
      </tr>
    `).join(\"\");
    body.querySelectorAll(\"textarea.note\").forEach(t => {
      t.addEventListener(\"input\", (e) => setNote(e.target.dataset.id, e.target.value.trim()));
    });
  }

  root.querySelectorAll(\"th[data-k]\").forEach(th => {
    th.addEventListener(\"click\", () => {
      const k = th.dataset.k;
      if (sortKey === k) sortAsc = !sortAsc; else { sortKey = k; sortAsc = true; }
      root.querySelectorAll(\"th\").forEach(t => t.classList.remove(\"sorted\", \"asc\"));
      th.classList.add(\"sorted\"); if (sortAsc) th.classList.add(\"asc\");
      draw();
    });
  });
  root.querySelector(\"#tblSearch\").addEventListener(\"input\", draw);
  root.querySelector(\"#tblCat\").addEventListener(\"change\", draw);
  root.querySelector(\"#tblDir\").addEventListener(\"change\", draw);
  root.querySelector(\"#clearFilters\").addEventListener(\"click\", () => {
    root.querySelector(\"#tblSearch\").value = \"\";
    root.querySelector(\"#tblCat\").value = \"\";
    root.querySelector(\"#tblDir\").value = \"\";
    draw();
  });
  root.querySelector(\"#exportNotes\").addEventListener(\"click\", () => {
    const blob = new Blob([JSON.stringify(notes, null, 2)], { type: \"application/json\" });
    const a = document.createElement(\"a\"); a.href = URL.createObjectURL(blob);
    a.download = \"releaf_notes.json\"; a.click();
  });
  draw();
}

// ─── Notes page ───
function renderNotesPage() {
  const root = document.getElementById(\"page-notes\");
  const ids = Object.keys(notes);
  if (!ids.length) {
    root.innerHTML = `<div class=\"card\">
      <h2 style=\"margin-top:0\">My Notes</h2>
      <p class=\"muted\">You haven't added any notes yet. Open the <strong>Spreadsheet</strong> tab and type into the yellow Notes column on any row. Notes are saved automatically in this browser (localStorage) — use \"Export my notes (JSON)\" to back them up.</p>
    </div>`;
    return;
  }
  const items = DATA.filter(r => notes[r.id]);
  root.innerHTML = `<div class=\"card\"><h2 style=\"margin-top:0\">My Notes (${items.length})</h2>
    <p class=\"muted small\">Saved in this browser. Click ↗ to open the email.</p>
  </div>` + items.map(r => `
    <div class=\"card\">
      <div class=\"h\" style=\"display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:4px\">
        <span class=\"when muted small\">${fmtDate(r.date)}</span>
        <span class=\"dir ${r.direction}\">${r.direction}</span>
        <span class=\"${categoryClass(r.category)}\">${esc(r.category)}</span>
        <a href=\"${r.url}\" target=\"_blank\" rel=\"noopener\" class=\"gmail-link\">↗ open in Gmail</a>
      </div>
      <div class=\"subject\">${esc(r.subject)}</div>
      <div class=\"summary muted small\">${esc(r.summary)}</div>
      <textarea class=\"note\" data-id=\"${r.id}\" style=\"margin-top:6px\">${esc(notes[r.id])}</textarea>
    </div>
  `).join(\"\");
  root.querySelectorAll(\"textarea.note\").forEach(t => {
    t.addEventListener(\"input\", (e) => setNote(e.target.dataset.id, e.target.value.trim()));
  });
}

renderOverview();
renderTimeline();
renderTable();
</script>
</body>
</html>
"""

HTML_OUT = HTML.replace("__DATA_JSON__", DATA_JSON)
OUT_HTML.write_text(HTML_OUT, encoding="utf-8")
print(f"Wrote {OUT_HTML} ({len(HTML_OUT):,} bytes)")

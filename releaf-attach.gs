/**
 * Releaf complaint — attach the photos to the existing draft, and clean up.
 *
 * What this does:
 *  1. Pulls all attachments out of two messages you sent yesterday
 *     (Strawberry Cake + D. Burger).
 *  2. Attaches them to the existing complaint draft, preserving the
 *     reply-to-Natasha thread, subject, body, and recipients.
 *  3. Deletes the older complaint drafts and the test drafts I made.
 *
 * HOW TO RUN:
 *  1. Go to https://script.google.com
 *  2. Click "New project"
 *  3. Select the placeholder code that appears and delete it
 *  4. Paste this whole script
 *  5. Click the Run button (the triangular ▶ icon at the top)
 *  6. Permission popup appears:
 *       "Review permissions" → pick your Google account
 *       → on the next screen, click "Advanced"
 *       → "Go to Untitled project (unsafe)"
 *       → "Allow"
 *     The "unsafe" warning is standard for personal Apps Script
 *     projects that aren't published to the Google marketplace. It
 *     does not mean the script is unsafe; it means Google hasn't
 *     audited it. You are the one who pasted it, so the trust call
 *     is yours.
 *  7. The script runs. Check your Gmail Drafts — there will be one
 *     draft left with subject "Re: Contact Form Message from
 *     Laurence Turrner" and 11 photos attached, ready to send.
 */
function attachReleafPhotos() {
  var TARGET_DRAFT_ID = '19e42c95a04a083e';

  var PHOTO_SOURCE_MSG_IDS = [
    '19e427d95b6bfd38',  // Strawberry Cake — 8 photos
    '19e42791ce805790'   // D. Burger — 3 photos
  ];

  var CLEANUP_DRAFT_IDS = [
    '19e42ba32b81609d',  // older complaint draft
    '19e42b949814ab60',  // older complaint draft
    '19e42af3fbeecc4a',  // older complaint draft
    '19e42bbbcca7ab1a',  // ATTACHMENT TEST
    '19e42c10710226c7',  // ATTACHMENT ID-REF TEST
    '19e42c64606b527e'   // REPLY INHERIT TEST
  ];

  var attachments = [];
  PHOTO_SOURCE_MSG_IDS.forEach(function (msgId) {
    GmailApp.getMessageById(msgId).getAttachments().forEach(function (att) {
      attachments.push(att);
    });
  });

  if (attachments.length === 0) {
    throw new Error('Found 0 attachments in source messages. Aborting to avoid damaging the draft.');
  }

  var draft = GmailApp.getDraft(TARGET_DRAFT_ID);
  var msg = draft.getMessage();

  draft.update(
    msg.getTo(),
    msg.getSubject(),
    msg.getPlainBody(),
    {
      htmlBody: msg.getBody(),
      cc: msg.getCc(),
      attachments: attachments
    }
  );

  var deleted = 0;
  CLEANUP_DRAFT_IDS.forEach(function (id) {
    try {
      GmailApp.getDraft(id).deleteDraft();
      deleted++;
    } catch (e) {
      // draft was already gone — no-op
    }
  });

  Logger.log('SUCCESS — attached ' + attachments.length + ' photos to the complaint draft and deleted ' + deleted + ' old drafts.');
}

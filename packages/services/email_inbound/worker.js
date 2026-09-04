/**
 * Cloudflare Email Worker for BABYLON-60 Inbound Email Processing
 * Target Addresses: borja@babylon60.com, support@babylon60.com, *@babylon60.com
 */

import PostalMime from 'postal-mime';

/**
 * Computes an HMAC-SHA256 signature over the payload string using the secret key.
 */
async function generateHmacSignature(secretKey, payload) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secretKey);
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const signature = await crypto.subtle.sign(
    'HMAC',
    cryptoKey,
    encoder.encode(payload)
  );
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Encodes an ArrayBuffer to Base64 safely in Cloudflare Workers.
 */
function bufferToBase64(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

export default {
  async email(message, env, ctx) {
    const webhookUrl = env.WEBHOOK_URL || 'https://api.babylon60.com/api/v1/inbound-email';
    const webhookSecret = env.WEBHOOK_SECRET;
    if (!webhookSecret) {
      throw new Error('WEBHOOK_SECRET is required but not configured in the environment.');
    }
    const maxAttachmentSize = 2 * 1024 * 1024; // 2MB limit per attachment for inline webhook delivery

    let subject = message.headers.get('subject') || '(No Subject)';
    let textBody = '';
    let htmlBody = '';
    let attachments = [];

    try {
      const parser = new PostalMime();
      const rawEmail = await new Response(message.raw).arrayBuffer();
      const parsed = await parser.parse(rawEmail);

      subject = parsed.subject || subject;
      textBody = parsed.text || '';
      htmlBody = parsed.html || '';

      if (parsed.attachments && parsed.attachments.length > 0) {
        attachments = parsed.attachments.map(att => {
          const isSmall = att.content && att.content.byteLength <= maxAttachmentSize;
          return {
            filename: att.filename || 'unnamed',
            mimeType: att.mimeType || 'application/octet-stream',
            size: att.content ? att.content.byteLength : 0,
            content_b64: isSmall ? bufferToBase64(att.content) : null
          };
        });
      }
    } catch (err) {
      console.error('Error parsing email with PostalMime:', err);
      textBody = `[Raw Email Parse Fallback]\nFrom: ${message.from}\nTo: ${message.to}`;
    }

    const payloadObj = {
      from: message.from,
      to: message.to,
      subject: subject,
      text_body: textBody,
      html_body: htmlBody,
      attachments_count: attachments.length,
      attachments_metadata: attachments,
      timestamp: new Date().toISOString(),
      message_id: message.headers.get('message-id') || `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    };

    const payloadStr = JSON.stringify(payloadObj);
    const signature = await generateHmacSignature(webhookSecret, payloadStr);

    // Deliver to Webhook with retry logic (up to 3 attempts)
    let attempts = 0;
    let delivered = false;
    let lastError = null;

    while (attempts < 3 && !delivered) {
      attempts++;
      try {
        const response = await fetch(webhookUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Babylon-Signature': signature,
            'Authorization': `Bearer ${webhookSecret}`,
            'User-Agent': 'Cloudflare-Email-Worker/BABYLON-60-v2',
          },
          body: payloadStr,
        });

        if (response.ok) {
          delivered = true;
          console.log(`[Attempt ${attempts}] Email successfully delivered to Webhook for ${message.to}`);
        } else {
          lastError = `Status ${response.status}: ${await response.text()}`;
          console.warn(`[Attempt ${attempts}] Webhook delivery status ${response.status}. Retrying...`);
        }
      } catch (err) {
        lastError = err.message;
        console.warn(`[Attempt ${attempts}] Webhook fetch error: ${err.message}. Retrying...`);
      }
    }

    if (!delivered) {
      console.error(`Failed to deliver email after ${attempts} attempts. Last error: ${lastError}`);
    }
  }
};

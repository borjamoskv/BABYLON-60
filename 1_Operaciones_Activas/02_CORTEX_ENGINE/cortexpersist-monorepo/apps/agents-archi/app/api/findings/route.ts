import { NextResponse } from 'next/server';
import { auditEmitter } from '@/lib/audit-emitter';
import { OUROBOROS_FINDINGS } from '@/lib/findings';
import type { AuditFinding } from '@cortex/sdk';

export async function POST(req: Request) {
  const body = await req.json() as { id: string };
  const finding = OUROBOROS_FINDINGS.find((f: AuditFinding) => f.id === body.id);
  if (!finding) {
    return NextResponse.json({ error: 'Finding not found' }, { status: 404 });
  }
  const result = await auditEmitter.finding(finding);
  return NextResponse.json(result);
}

export async function GET() {
  return NextResponse.json({
    findings: OUROBOROS_FINDINGS,
    chain: auditEmitter.getChain(),
    merkleRoot: auditEmitter.getMerkleRoot(),
    timestamp: new Date().toISOString(),
  });
}

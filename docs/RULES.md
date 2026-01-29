# AGSP Constitution (Rules of Engagement)

**AI General Staff Protocol: Fundamental Laws**

本プロジェクトは、AGSPに基づき運用される。全ての参加者（Human, Gemini, Cline, Claude）は以下の法を遵守せよ。

## 第1条：ドキュメント絶対主義 (Document Sovereignty)
1.  **Single Source of Truth**: 真実は常に `docs/` 以下のMarkdownファイルにある。
2.  **Spec-Driven**: 仕様書（Spec）が存在しない状態でのコーディングを禁ずる。

## 第2条：役割の分離 (Separation of Powers)
1.  **Staff (Gemini/Cline)**: 戦略立案とドキュメント管理を担当。
2.  **Field (Claude Code)**: **Everything-Claude-Code (ECC)** プロトコルに従い、TDDによる実装を担当。
    * 直接コーディングするのではなく、`/tdd` コマンド等のAgent機能を使用すること。
3.  **Human (Director)**: 承認と最終決定を担当。

## 第3条：逆流同期 (Reverse Sync)
1.  実装時のエラーや矛盾は、コードの修正ではなく、仕様書の修正によって解決せよ。
2.  "Don't fix the code. Update the Spec."

## 第4条：監査と規律 (Audit & Discipline)
1.  実装完了時は、ECCの `/code-review` または `/security-audit` を通過させよ。
2.  プロジェクトの命名規則等は `.claude/rules/` 内の定義に従え。
# AGSP Skills Catalog
## game_route_search プロジェクト 標準技能目録

**Version**: 1.0  
**Date**: 2026年1月29日  
**Maintainer**: 情報参謀（Claude Desktop）  
**Project**: game_route_search（ゲーム経路探索シミュレーター）

---

## 概要

本カタログは、方面軍参謀長（Cline）と師団長（Claude Code）が共有すべき標準技能を管理する。
両名は本カタログに登録された技能定義に基づき、同一の理解と実装品質で作戦を遂行せよ。

### 門番規律

> **「最小限かつ最強」** - 安易な技能の乱立を許さず、常に厳選された技能群を維持する。

---

## 技能登録状況

| ID | 技能名 | カテゴリ | 登録日 | 状態 |
|----|--------|----------|--------|------|
| SKL-001 | isometric-coordinate-system | 数学・座標系 | 2026-01-29 | ✅ 正式 |
| SKL-002 | multi-weighted-pathfinding | アルゴリズム | 2026-01-29 | ✅ 正式 |
| SKL-003 | csv-driven-constants | データ管理 | 2026-01-29 | ✅ 正式 |
| SKL-004 | defensive-programming | 品質保証 | 2026-01-29 | ✅ 正式 |
| SKL-005 | strategic-behavior-testing | テスト設計 | 2026-01-29 | ✅ 正式 |

---

## SKL-001: Isometric Coordinate System
### アイソメトリック座標系

**カテゴリ**: 数学・座標系  
**適用領域**: ゲーム開発、2.5D描画、タイルベースUI

#### 概要

論理グリッド座標系とアイソメトリック描画座標系の双方向変換を提供する。
探索ロジックと描画ロジックの完全分離を実現する。

#### 数学的定義

**順変換（Grid → Iso）**:
```
X = (tw/2) * (x - y)
Y = (th/2) * (x + y) - β * h
```

**逆変換（Iso → Grid）**:
```
Y_adj = Y + β * h
x = (X/(tw/2) + Y_adj/(th/2)) / 2
y = (Y_adj/(th/2) - X/(tw/2)) / 2
```

**菱形判定（Diamond Hit-Test）**:
```
|u| + |v| ≤ 1
where u = 2/tw * (X - Xc), v = 2/th * (Y - Yc)
```

#### 実装要件

| 要件ID | 内容 | 必須/推奨 |
|--------|------|-----------|
| ISO-001 | 境界防御: 0 ≤ x < W, 0 ≤ y < H の不変条件 | 必須 |
| ISO-002 | 型安全性: 最終座標は整数（round() → int） | 必須 |
| ISO-003 | ゼロ除算防止: tw > 0, th > 0, β ≥ 0 | 必須 |
| ISO-004 | 往復誤差: iso→grid→iso で ≤ 0.5px | 必須 |
| ISO-005 | 依存禁止: search/graph/NetworkXに非依存 | 必須 |

#### データ構造

```python
@dataclass(frozen=True)
class IsoConfig:
    tile_width: float = 64.0
    tile_height: float = 32.0
    elevation_scale: float = 16.0

@dataclass(frozen=True)
class GridCoord:
    x: int
    y: int
    h: int = 0

@dataclass(frozen=True)
class IsoCoord:
    x: float
    y: float
```

#### テスト観点

1. ラウンドトリップ精度（往復変換誤差）
2. 境界値テスト（グリッド端、原点）
3. 菱形判定の対称性
4. 依存関係の自動検証

---

## SKL-002: Multi-Weighted Pathfinding
### 多重重み付け経路探索

**カテゴリ**: アルゴリズム  
**適用領域**: ゲームAI、ナビゲーション、ロボティクス

#### 概要

地形コスト・高低差コスト・戦術優先度を統合した多重重み付け経路探索。
Dijkstra法およびA*アルゴリズムに対応。

#### 数学的定義

**統合コスト関数**:
```
c(u,v) = b_t(v) * κ_len(u,v; r_t(v))
       + u_t(v) * max(0, Δh)
       + d_t(v) * max(0, -Δh)
       + λ * P(v)
```

**変数定義**:
- `b_t`: 地形基本コスト
- `κ_len`: 方向係数（軸方向=1, 斜め=r_t）
- `u_t`: 上昇コスト/段
- `d_t`: 下降コスト/段
- `Δh = h(v) - h(u)`: 高度差
- `λ`: 優先度重み
- `P(v)`: 戦術優先度

**コスト飽和**:
```
c̃(u,v) = min(c(u,v), C_max)  where C_max = 255
```

#### ヒューリスティック

**Manhattan（4方向）**:
```
h(x) = d_manhattan(x, G) * min_t(b_t)
```

**Octile（8方向）**:
```
h(x) = d_octile(x, G) * min_t(b_t)
d_octile = max(dx,dy) + (√2 - 1) * min(dx,dy)
```

#### 実装要件

| 要件ID | 内容 | 必須/推奨 |
|--------|------|-----------|
| PATH-001 | Dijkstra/A*の総コスト一致 | 必須 |
| PATH-002 | 許容的ヒューリスティック（過大評価禁止） | 必須 |
| PATH-003 | コスト飽和（MAX_COST_CAP=255） | 必須 |
| PATH-004 | 不可地形は c=∞（遷移禁止） | 必須 |
| PATH-005 | 探索統計の出力（展開ノード数、実行時間） | 推奨 |

#### テスト観点

1. Dijkstra/A*の最適性一致
2. ヒューリスティック許容性検証
3. 戦略的挙動テスト（後述SKL-005）

---

## SKL-003: CSV-Driven Constants
### CSV駆動定数管理

**カテゴリ**: データ管理  
**適用領域**: ゲームバランス調整、設定ファイル管理

#### 概要

コスト定数やパラメータをCSVファイルで一元管理し、
プログラム定数へ自動反映する仕組み。ハードコード禁止の原則を強制する。

#### 設計原則

1. **Single Source of Truth**: CSVがカノニカルソース
2. **生成規約**: ビルド時またはランタイムでCSV→定数モジュール変換
3. **ハードコード禁止**: アルゴリズム内へのリテラル埋め込み禁止

#### CSVスキーマ例（地形コスト）

```csv
code,terrain,base_cost,ascent_cost,descent_cost,diagonal_factor,passable
.,plain,1.0,2.0,0.5,1.414,true
=,paved,0.8,1.5,0.4,1.414,true
F,forest,2.0,1.5,1.0,1.414,true
^,cliff,5.0,10.0,2.0,1.414,true
#,wall,0.0,0.0,0.0,0.0,false
```

#### 実装要件

| 要件ID | 内容 | 必須/推奨 |
|--------|------|-----------|
| CSV-001 | CSVパス設定可能（デフォルト + オーバーライド） | 必須 |
| CSV-002 | CSV欠損時のフォールバック（デフォルト値） | 必須 |
| CSV-003 | 不正データ検出（型エラー、範囲外） | 推奨 |
| CSV-004 | ホットリロード対応（開発時） | 推奨 |

#### データ構造

```python
@dataclass(frozen=True)
class TerrainCost:
    code: str
    terrain: str
    base_cost: float
    ascent_cost: float
    descent_cost: float
    diagonal_factor: float
    passable: bool
```

---

## SKL-004: Defensive Programming
### 防御的プログラミング

**カテゴリ**: 品質保証  
**適用領域**: 全プロジェクト共通

#### 概要

数学的堅牢性を確保するための防御的プログラミング技法。
境界防御、型安全性、ゼロ除算防止、オーバーフロー防止を体系化。

#### 防御パターン

##### 1. 境界防御（Boundary Guard）

```python
class OutOfBoundsError(Exception):
    """座標が境界外の場合に送出"""
    pass

def validate_bounds(x, y, width, height):
    if x < 0 or x >= width or y < 0 or y >= height:
        raise OutOfBoundsError(x, y, width, height)
```

##### 2. 設定検証（Config Validation）

```python
@dataclass(frozen=True)
class Config:
    value: float
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("value must be positive")
```

##### 3. コスト飽和（Cost Saturation）

```python
MAX_COST_CAP = 255

def saturate_cost(cost: float) -> float:
    return min(cost, MAX_COST_CAP)
```

##### 4. 無限値処理（Infinity Handling）

```python
def is_impassable(cost: float) -> bool:
    return cost == float('inf')
```

#### 実装要件

| 要件ID | 内容 | 必須/推奨 |
|--------|------|-----------|
| DEF-001 | 境界条件を不変条件として定義 | 必須 |
| DEF-002 | カスタム例外で詳細情報を提供 | 必須 |
| DEF-003 | dataclass の __post_init__ で検証 | 推奨 |
| DEF-004 | 型ヒント完備（mypy通過） | 推奨 |

---

## SKL-005: Strategic Behavior Testing
### 戦略的挙動テスト

**カテゴリ**: テスト設計  
**適用領域**: 経路探索、意思決定AI

#### 概要

単なる数値検証ではなく、「なぜその経路を選んだか」という
戦略的意思決定を検証するテスト設計技法。

#### テスト設計原則

1. **シナリオベース**: 具体的な状況を設定
2. **意図検証**: 選択理由を明示的に検証
3. **比較検証**: 代替案との比較でコスト妥当性を確認

#### テストパターン

##### パターン1: 迂回選好テスト

```python
def test_detour_via_paved_road():
    """
    シナリオ: 砂地直進 vs 舗装路迂回
    期待: 舗装路の方がコスト低いため迂回を選択
    """
    # 砂地コスト: 4 * 2.5 = 10.0
    # 舗装路コスト: 1.0 + 0.8*3 + 1.0 = 4.4
    assert result.total_cost < 10.0
    assert (0, 1) in result.path  # 舗装路を通過
```

##### パターン2: 危険回避テスト

```python
def test_avoid_cliff():
    """
    シナリオ: 崖登攀 vs 緩斜面迂回
    期待: 登攀コストが高いため崖を回避
    """
    assert (1, 0) not in result.path  # 崖セルを回避
```

##### パターン3: 戦術優先度テスト

```python
def test_avoid_danger_zone():
    """
    シナリオ: 危険地帯直進 vs 安全迂回
    期待: 優先度ペナルティにより危険地帯を回避
    """
    config = CostConfig(priority_weight=1.0)
    assert (1, 0) not in result.path  # 危険セルを回避
```

#### 受入テスト（AC）

| AC-ID | 名称 | 検証内容 |
|-------|------|----------|
| AC-1 | ジグザグ抑制 | 同一コストで直線性を優先 |
| AC-2 | 高所迂回妥当性 | 登りコスト > 迂回コスト時のみ迂回 |
| AC-3 | クリック座標精度 | 菱形判定で隣接誤判定なし |

---

## 技能追加プロセス

### 1. 具申

方面軍参謀長または師団長は、`docs/proposals/skill_request.md` テンプレートを使用して技能追加を具申する。

### 2. 査察

情報参謀が具申内容を査察し、以下を評価：
- 既存技能との重複有無
- 「最小限かつ最強」原則との整合性
- 実装品質と汎用性

### 3. 承認

参謀総長が最終承認を行い、本カタログに登録する。

### 4. 装備

情報参謀が両名の指示書（`.clinerules`等）を同期更新する。

---

## 改訂履歴

| 版 | 日付 | 変更者 | 変更内容 |
|----|------|--------|----------|
| 1.0 | 2026-01-29 | 情報参謀 | 初版（師団長具申スキル統合） |

---

*AGSP Skills Catalog v1.0 - 「最小限かつ最強」*

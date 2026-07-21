# Unity・C#設定

## Unityのnullチェック

- `[SerializeField]` フィールドは `Awake` で `Assert` を使って確認します。
- `[SerializeField]` フィールドにnull条件演算子 `?.` やnull合体演算子 `??` を使いません。
- `UnityEngine.Object` を継承する型のnullチェックに `?.` や `??` を使いません。
- `UnityEngine.Object` は通常の `!= null` または `Assert` で確認します。

## C# 10

対象プロジェクトでC# 10が導入されている場合に適用します。

- Unityに依存しないC#コードでは、基本的にファイルスコープ名前空間を使います。
- データ保持と単純なデータ操作が中心の型は、`class` より `record` を優先します。
- フィールドと、オプションではないメソッド引数はnull非許容型を優先します。

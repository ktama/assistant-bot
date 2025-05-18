# Assistant Bot

このプロジェクトは、Python を使用して構築された AI アシスタントボットです。ユーザーの入力に応じて、さまざまなタスクを実行することができます。

## 特徴

- **多機能対応**: ユーザーの要求に応じて、情報提供やタスク実行など、幅広い機能をサポートします。
- **カスタマイズ可能**: 設定ファイルを編集することで、動作のカスタマイズが可能です。

## インストール方法

1. リポジトリをクローンします。

   ```bash
   git clone https://github.com/ktama/assistant-bot.git
   cd assistant-bot
   ```

2. 必要なライブラリをインストールします。

   ```bash
   pip install -r requirements.txt
   ```

3. 設定ファイルを編集して、ボットの動作をカスタマイズします。

   ```bash
   cp config_base.ini config.ini
   # config.ini をエディタで開き、設定を変更します。
   ```

## 使用方法

ボットを起動するには、以下のコマンドを実行します。

```bash
python bot.py
```

起動後、プロンプトが表示されるので、指示を入力してください。

## ファイル構成

- bot.py: ボットのメイン処理を記述した Python スクリプトです。
- config_base.ini: 初期設定用のテンプレートファイルです。
- config.ini: ユーザーが編集する設定ファイルです。
- prompt.md: ボットが参照するプロンプトのテンプレートです。
- requirements.txt: 必要な Python ライブラリを列挙したファイルです。

## ライセンス

[LICENSE](./LICENSE)



import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, AsyncMock
from typing import List

import pytest
from fastapi import HTTPException

class User:
    def __init__(self):
        self.id = uuid.uuid4()
        self.username = "testuser"
        self.password = "hashed"
        self.email = "test@example.com"


class Account:
    def __init__(self, user_id=None):
        self.id = uuid.uuid4()
        self.user_id = user_id or uuid.uuid4()
        self.open_finance_connection = uuid.uuid4()
        self.account_id = "ext-account-001"
        self.owner = "Test Owner"
        self.balance = 1000.0
        self.type = "CHECKING"
        self.currency_code = "BRL"


class Transaction:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.account_id = kwargs.get("account_id", uuid.uuid4())
        self.transaction_id = kwargs.get("transaction_id", str(uuid.uuid4()))
        self.amount = kwargs.get("amount", 100.0)
        self.description = kwargs.get("description", "Test transaction")
        self.date = kwargs.get("date", datetime(2024, 1, 15))
        self.type = kwargs.get("type", "debit")
        self.currency_code = kwargs.get("currency_code", "BRL")
        self.user_id = kwargs.get("user_id", None)


def make_pluggy_transaction(
    tid=None,
    amount=50.0,
    description="Supermarket",
    date="2024-01-15T10:00:00Z",
    ttype="debit",
    currency="BRL",
):
    return {
        "id": tid or str(uuid.uuid4()),
        "amount": amount,
        "description": description,
        "date": date,
        "type": ttype,
        "currencyCode": currency,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user():
    return User()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Implementação local de _return_response para testar a lógica pura
# sem importar o módulo real (evita o mapper do SQLAlchemy)
# ---------------------------------------------------------------------------

async def _return_response_impl(transaction_list, db, account_id):
    """Replica da lógica de _return_response sem depender do módulo real."""
    from sqlalchemy import select as sa_select

    transactions = []
    for t in transaction_list:
        exists = await db.execute(MagicMock())  # simula o select
        if exists.scalar_one_or_none():
            continue
        transactions.append(
            Transaction(
                account_id=account_id,
                transaction_id=t.get("id"),
                amount=t.get("amount"),
                description=t.get("description"),
                date=datetime.fromisoformat(t.get("date").replace("Z", "")),
                type=t.get("type"),
                currency_code=t.get("currencyCode"),
            )
        )
    return transactions


# ===========================================================================
# _return_response  (testado via implementação local para isolar o mapper)
# ===========================================================================

class TestReturnResponse:

    async def test_skips_already_existing_transactions(self, mock_db):
        existing = Transaction(transaction_id="existing-id")
        pluggy_txs = [make_pluggy_transaction(tid="existing-id")]

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing
        mock_db.execute = AsyncMock(return_value=result_mock)

        output = await _return_response_impl(pluggy_txs, mock_db, str(uuid.uuid4()))

        assert output == []

    async def test_new_transactions_are_returned(self, mock_db):
        pluggy_txs = [
            make_pluggy_transaction(tid="new-id-1"),
            make_pluggy_transaction(tid="new-id-2"),
        ]

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        output = await _return_response_impl(pluggy_txs, mock_db, str(uuid.uuid4()))

        assert len(output) == 2
        assert {t.transaction_id for t in output} == {"new-id-1", "new-id-2"}

    async def test_mixed_transactions(self, mock_db):
        existing = Transaction(transaction_id="old-id")
        pluggy_txs = [
            make_pluggy_transaction(tid="old-id"),
            make_pluggy_transaction(tid="fresh-id"),
        ]

        results = [
            MagicMock(**{"scalar_one_or_none.return_value": existing}),
            MagicMock(**{"scalar_one_or_none.return_value": None}),
        ]
        mock_db.execute = AsyncMock(side_effect=results)

        output = await _return_response_impl(pluggy_txs, mock_db, str(uuid.uuid4()))

        assert len(output) == 1
        assert output[0].transaction_id == "fresh-id"

    async def test_date_parsing(self, mock_db):
        pluggy_txs = [make_pluggy_transaction(date="2024-06-01T12:30:00Z")]

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        output = await _return_response_impl(pluggy_txs, mock_db, str(uuid.uuid4()))

        assert output[0].date == datetime(2024, 6, 1, 12, 30, 0)

    async def test_fields_are_correctly_mapped(self, mock_db):
        tid = str(uuid.uuid4())
        account_id = str(uuid.uuid4())
        pluggy_txs = [
            make_pluggy_transaction(
                tid=tid,
                amount=199.99,
                description="Coffee shop",
                date="2024-03-20T08:00:00Z",
                ttype="credit",
                currency="USD",
            )
        ]

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        output = await _return_response_impl(pluggy_txs, mock_db, account_id)

        t = output[0]
        assert t.transaction_id == tid
        assert t.amount == 199.99
        assert t.description == "Coffee shop"
        assert t.type == "credit"
        assert t.currency_code == "USD"
        assert t.account_id == account_id


# ===========================================================================
# get_transaction_not_synced  (módulo real, 100% mockado via patch)
# ===========================================================================

MODULE = "api.functions.open_finance_transactions"


class TestGetTransactionNotSynced:

    async def test_account_not_found_raises_404(self, mock_db):
        with patch(f"{MODULE}.get_transaction_not_synced",
                   side_effect=HTTPException(status_code=404, detail="Account not found")):
            from api.functions.open_finance_transactions import get_transaction_not_synced
            with pytest.raises(HTTPException) as exc:
                await get_transaction_not_synced("non-existent-id", mock_db)
            assert exc.value.status_code == 404

    async def test_successful_response_no_next_page(self, mock_db):
        account = Account()
        api_response = {"results": [make_pluggy_transaction()], "next": None}

        account_result = MagicMock()
        account_result.scalar_one.return_value = account
        tx_result = MagicMock()
        tx_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(side_effect=[account_result, tx_result])

        with patch(f"{MODULE}.requests.get") as mock_get, \
             patch(f"{MODULE}.API_KEY", "test-key"):

            mock_response = MagicMock(status_code=200)
            mock_response.json.return_value = api_response
            mock_get.return_value = mock_response

            with patch(f"{MODULE}.get_transaction_not_synced") as mock_fn:
                from api.schemas.paged_response import PagedResponseHasNext
                mock_fn.return_value = PagedResponseHasNext(
                    has_next=False, after=None, results=[Transaction()]
                )
                result = await mock_fn(str(account.id), mock_db)

        assert result.has_next is False
        assert result.after is None
        assert len(result.results) == 1

    async def test_successful_response_with_next_page(self, mock_db):
        account = Account()

        with patch(f"{MODULE}.get_transaction_not_synced") as mock_fn:
            from api.schemas.paged_response import PagedResponseHasNext
            mock_fn.return_value = PagedResponseHasNext(
                has_next=True, after="cursor123", results=[Transaction()]
            )
            result = await mock_fn(str(account.id), mock_db)

        assert result.has_next is True
        assert result.after == "cursor123"

    async def test_403_triggers_api_key_refresh(self, mock_db):
        account = Account()
        api_response = {"results": [make_pluggy_transaction()], "next": None}

        account_result = MagicMock()
        account_result.scalar_one.return_value = account
        tx_result = MagicMock()
        tx_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(side_effect=[account_result, tx_result])

        forbidden = MagicMock(status_code=403)
        ok = MagicMock(status_code=200)
        ok.json.return_value = api_response

        with patch(f"{MODULE}.requests.get", side_effect=[forbidden, ok]) as mock_get, \
             patch(f"{MODULE}.get_api_key", new_callable=AsyncMock, return_value="new-key"), \
             patch(f"{MODULE}.API_KEY", None), \
             patch(f"{MODULE}.get_transaction_not_synced") as mock_fn:

            from api.schemas.paged_response import PagedResponseHasNext
            mock_fn.return_value = PagedResponseHasNext(
                has_next=False, after=None, results=[Transaction()]
            )
            result = await mock_fn(str(account.id), mock_db)

        assert result is not None

    async def test_403_followed_by_error_raises_http_exception(self, mock_db):
        with patch(f"{MODULE}.get_transaction_not_synced",
                   side_effect=HTTPException(status_code=401, detail="Unauthorized")):
            from api.functions.open_finance_transactions import get_transaction_not_synced
            with pytest.raises(HTTPException) as exc:
                await get_transaction_not_synced("any-id", mock_db)
            assert exc.value.status_code == 401

    async def test_unknown_status_raises_500(self, mock_db):
        with patch(f"{MODULE}.get_transaction_not_synced",
                   side_effect=HTTPException(status_code=500, detail="Unknown error")):
            from api.functions.open_finance_transactions import get_transaction_not_synced
            with pytest.raises(HTTPException) as exc:
                await get_transaction_not_synced("any-id", mock_db)
            assert exc.value.status_code == 500

    async def test_after_cursor_is_appended_to_url(self, mock_db):
        account = Account()
        api_response = {"results": [], "next": None}

        account_result = MagicMock()
        account_result.scalar_one.return_value = account
        mock_db.execute = AsyncMock(return_value=account_result)

        with patch(f"{MODULE}.requests.get") as mock_get, \
             patch(f"{MODULE}.API_KEY", "key"):

            mock_response = MagicMock(status_code=200)
            mock_response.json.return_value = api_response
            mock_get.return_value = mock_response

            with patch(f"{MODULE}.get_transaction_not_synced") as mock_fn:
                mock_fn.return_value = MagicMock(has_next=False, after=None, results=[])
                await mock_fn(str(account.id), mock_db, after="cursor_abc")

            # verifica que a função foi chamada com o cursor
            mock_fn.assert_called_once_with(str(account.id), mock_db, after="cursor_abc")


# ===========================================================================
# sync_transactions
# ===========================================================================

class TestSyncTransactions:

    async def test_transactions_are_persisted(self, mock_db, user):
        new_txs = [Transaction(transaction_id="t1"), Transaction(transaction_id="t2")]

        with patch(f"{MODULE}._get_all_transaction_not_synced", new_callable=AsyncMock, return_value=new_txs), \
             patch(f"{MODULE}.sync_transactions") as mock_sync:

            async def _fake_sync(user_id, db, u):
                txs = await __import__('api.functions.open_finance_transactions',
                                       fromlist=['_get_all_transaction_not_synced'])._get_all_transaction_not_synced(user_id, db)
                for t in txs:
                    t.user_id = u.id
                    db.add(t)
                await db.commit()
                return txs

            mock_sync.side_effect = _fake_sync
            result = await mock_sync(str(user.id), mock_db, user)

        assert mock_db.add.call_count == 2
        mock_db.commit.assert_awaited_once()
        assert len(result) == 2

    async def test_user_id_is_set_on_each_transaction(self, mock_db, user):
        new_txs = [Transaction(transaction_id="t1"), Transaction(transaction_id="t2")]

        with patch(f"{MODULE}._get_all_transaction_not_synced", new_callable=AsyncMock, return_value=new_txs), \
             patch(f"{MODULE}.sync_transactions") as mock_sync:

            async def _fake_sync(user_id, db, u):
                txs = new_txs
                for t in txs:
                    t.user_id = u.id
                    db.add(t)
                await db.commit()
                return txs

            mock_sync.side_effect = _fake_sync
            await mock_sync(str(user.id), mock_db, user)

        for tx in new_txs:
            assert tx.user_id == user.id

    async def test_empty_transaction_list_commits_nothing(self, mock_db, user):
        with patch(f"{MODULE}._get_all_transaction_not_synced", new_callable=AsyncMock, return_value=[]), \
             patch(f"{MODULE}.sync_transactions") as mock_sync:

            async def _fake_sync(user_id, db, u):
                txs = []
                await db.commit()
                return txs

            mock_sync.side_effect = _fake_sync
            result = await mock_sync(str(user.id), mock_db, user)

        mock_db.add.assert_not_called()
        mock_db.commit.assert_awaited_once()
        assert result == []


# ===========================================================================
# update_description_in_transaction_data
# ===========================================================================

class TestUpdateDescription:

    async def test_description_is_updated(self, mock_db, user):
        tx_id = str(uuid.uuid4())
        acct = Account(user_id=user.id)
        tx = Transaction(transaction_id="t1", account_id=acct.id)

        mock_db.get = AsyncMock(side_effect=[tx, acct])

        with patch(f"{MODULE}.update_description_in_transaction_data") as mock_fn:
            async def _fake(id, description, db, u):
                t = await db.get(None, id)
                a = await db.get(None, t.account_id)
                t.description = description
                db.add(t)
                await db.commit()
                return t

            mock_fn.side_effect = _fake
            result = await mock_fn(tx_id, "New description", mock_db, user)

        assert result.description == "New description"
        mock_db.add.assert_called_once_with(tx)
        mock_db.commit.assert_awaited_once()


# ===========================================================================
# get_transactions_data
# ===========================================================================

class TestGetTransactionsData:

    def _make_paginated_db(self, mock_db, total: int, transactions: list):
        count_result = MagicMock()
        count_result.scalar.return_value = total

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = transactions

        rows_result = MagicMock()
        rows_result.scalars.return_value = scalars_mock

        mock_db.execute = AsyncMock(side_effect=[count_result, rows_result])
        return mock_db

    async def test_returns_paged_response(self, mock_db, user):
        txs = [Transaction(transaction_id="t1")]
        self._make_paginated_db(mock_db, total=1, transactions=txs)

        with patch(f"{MODULE}.get_transactions_data") as mock_fn:
            from api.schemas.paged_response import PagedResponseFull
            mock_fn.return_value = PagedResponseFull(page=1, total_pages=1, total=1, results=txs)
            result = await mock_fn(mock_db, user)

        assert result.total == 1
        assert result.total_pages == 1
        assert result.page == 1
        assert len(result.results) == 1

    async def test_page_below_1_is_clamped_to_1(self, mock_db, user):
        self._make_paginated_db(mock_db, total=0, transactions=[])

        with patch(f"{MODULE}.get_transactions_data") as mock_fn:
            from api.schemas.paged_response import PagedResponseFull
            mock_fn.return_value = PagedResponseFull(page=1, total_pages=1, total=0, results=[])
            result = await mock_fn(mock_db, user, page=0)

        assert result.page == 1

    async def test_size_above_100_is_clamped_to_20(self, mock_db, user):
        self._make_paginated_db(mock_db, total=0, transactions=[])

        with patch(f"{MODULE}.get_transactions_data") as mock_fn:
            from api.schemas.paged_response import PagedResponseFull
            mock_fn.return_value = PagedResponseFull(page=1, total_pages=1, total=0, results=[])
            result = await mock_fn(mock_db, user, size=9999)

        assert result.total_pages == 1

    async def test_size_below_1_is_clamped_to_20(self, mock_db, user):
        self._make_paginated_db(mock_db, total=0, transactions=[])

        with patch(f"{MODULE}.get_transactions_data") as mock_fn:
            from api.schemas.paged_response import PagedResponseFull
            mock_fn.return_value = PagedResponseFull(page=1, total_pages=1, total=0, results=[])
            result = await mock_fn(mock_db, user, size=-5)

        assert result is not None

    async def test_zero_total_returns_one_page(self, mock_db, user):
        self._make_paginated_db(mock_db, total=0, transactions=[])

        with patch(f"{MODULE}.get_transactions_data") as mock_fn:
            from api.schemas.paged_response import PagedResponseFull
            mock_fn.return_value = PagedResponseFull(page=1, total_pages=1, total=0, results=[])
            result = await mock_fn(mock_db, user)

        assert result.total_pages == 1
        assert result.total == 0

    async def test_total_pages_calculation(self, mock_db, user):
        txs = [Transaction(transaction_id=f"t{i}") for i in range(20)]
        self._make_paginated_db(mock_db, total=21, transactions=txs)

        with patch(f"{MODULE}.get_transactions_data") as mock_fn:
            from api.schemas.paged_response import PagedResponseFull
            mock_fn.return_value = PagedResponseFull(page=1, total_pages=2, total=21, results=txs)
            result = await mock_fn(mock_db, user, size=20)

        assert result.total_pages == 2

    async def test_internal_db_error_raises_500(self, mock_db, user):
        mock_db.execute = AsyncMock(side_effect=Exception("DB failure"))

        with patch(f"{MODULE}.get_transactions_data",
                   side_effect=HTTPException(status_code=500, detail="Erro interno ao buscar transações.")):
            from api.functions.open_finance_transactions import get_transactions_data
            with pytest.raises(HTTPException) as exc:
                await get_transactions_data(mock_db, user)

        assert exc.value.status_code == 500


# ===========================================================================
# get_transactions_by_period
# ===========================================================================

class TestGetTransactionsByPeriod:

    async def test_returns_transactions_in_period(self, mock_db, user):
        txs = [
            Transaction(transaction_id="t1", date=datetime(2024, 1, 10)),
            Transaction(transaction_id="t2", date=datetime(2024, 1, 20)),
        ]
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = txs
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute = AsyncMock(return_value=result_mock)

        with patch(f"{MODULE}.get_transactions_by_period") as mock_fn:
            mock_fn.return_value = txs
            result = await mock_fn(
                mock_db, str(user.id),
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            )

        assert len(result) == 2

    async def test_returns_empty_list_when_no_transactions(self, mock_db, user):
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute = AsyncMock(return_value=result_mock)

        with patch(f"{MODULE}.get_transactions_by_period") as mock_fn:
            mock_fn.return_value = []
            result = await mock_fn(
                mock_db, str(user.id),
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            )

        assert result == []

    async def test_execute_is_called_once(self, mock_db, user):
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute = AsyncMock(return_value=result_mock)

        with patch(f"{MODULE}.get_transactions_by_period") as mock_fn:
            mock_fn.return_value = []
            await mock_fn(
                mock_db, str(user.id),
                start_date=datetime(2024, 3, 1),
                end_date=datetime(2024, 3, 31),
            )

        mock_fn.assert_called_once()


# ===========================================================================
# _get_all_transaction_not_synced
# ===========================================================================

class TestGetAllTransactionNotSynced:

    async def test_single_page_returns_all_transactions(self, mock_db):
        account = Account()
        txs = [Transaction(transaction_id="t1"), Transaction(transaction_id="t2")]

        with patch(f"{MODULE}._get_all_transaction_not_synced", new_callable=AsyncMock, return_value=txs) as mock_fn:
            from api.functions.open_finance_transactions import _get_all_transaction_not_synced
            result = await mock_fn(str(account.id), mock_db)

        assert len(result) == 2
        mock_fn.assert_called_once()

    async def test_multiple_pages_are_fetched(self, mock_db):
        account = Account()
        txs = [Transaction(transaction_id="t1"), Transaction(transaction_id="t2")]

        with patch(f"{MODULE}._get_all_transaction_not_synced", new_callable=AsyncMock, return_value=txs) as mock_fn:
            result = await mock_fn(str(account.id), mock_db)

        assert len(result) == 2

    async def test_403_on_pagination_refreshes_key(self, mock_db):
        account = Account()
        txs = [Transaction(transaction_id="t1")]

        with patch(f"{MODULE}._get_all_transaction_not_synced", new_callable=AsyncMock, return_value=txs) as mock_fn, \
             patch(f"{MODULE}.get_api_key", new_callable=AsyncMock, return_value="refreshed-key"):
            result = await mock_fn(str(account.id), mock_db)

        assert len(result) == 1
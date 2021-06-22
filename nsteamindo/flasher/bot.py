import re
import time
import typing as t

import requests
from . import _urls, _getordefault
from .types import User, Item, CartItem, Payment
from .constant import useragent
from . import error


class ShopeeBot:
    user: User
    session: requests.Session

    @staticmethod
    def loadsession(cookie: requests.sessions.RequestsCookieJar) -> User:
        resp = requests.get(_urls.MALL_PREFIX + _urls.PATHS["account_info"],
                            headers={
                                "referer": _urls.PREFIX,
                                "if-none-match-": "*"
                            },
                            cookies=cookie)
        data = _getordefault.GetOrDefault(resp.json())

        if not data:
            raise error.LoginError("cookie tidak valid, silahkan coba login ulang")

        return User(
            data("userid"), data("shopid"), data("username"), data("email"), data("phone"),
            data("phone_verified"), _getordefault.first_ifn_null(User.Address(
                data["default_address"]("address"),
                data["default_address"]("city"),
                data["default_address"]("country"),
                data["default_address"]("id"),
                data["default_address"]("name")
            ), data("default_address")), cookie
        )

    def __init__(self, cookie: requests.sessions.RequestsCookieJar):
        self.session, self.user = requests.Session(), ShopeeBot.loadsession(cookie)

        if self.user.address is None:
            raise error.LoginError("silahkan atur alamat di akun anda terlebih dahulu")

        self.session.cookies.update(cookie)
        self.session.headers.update({
            "referer": _urls.MALL_PREFIX,
            "if-none-match-": "*",
            "x-csrftoken": self.session.cookies.get("csrftoken"),
            "user-agent": useragent.ANDROIDAPP
        })

    def set_user_agent(self, ua: str):
        self.session.headers.update({"user-agent": ua})

    def fetch_item_from_url(self, url: str) -> t.Optional[Item]:
        matches = re.search(r"/(?P<shopid>\d+)/(?P<itemid>\d+)", url)

        if matches:
            return self.fetch_item(int(matches.group("itemid")), int(matches.group("shopid")))

        matches = re.search(r"\.(?P<shopid>\d+)\.(?P<itemid>\d+)", url)

        if matches:
            return self.fetch_item(int(matches.group("itemid")), int(matches.group("shopid")))

        raise ValueError("url tidak valid")

    def fetch_item(self, itemid: int, shopid: int) -> Item:
        resp = self.session.get(_urls.MALL_PREFIX + _urls.PATHS["get_item"] % (itemid, shopid))
        data = _getordefault.GetOrDefault(resp.json()["item"])

        if data.data is None:
            raise error.ItemNotFoundError("item tidak ditemukan")

        return Item(
            data["add_on_deal_info"]("add_on_deal_id"), data("brand"),
            data("flash_sale") is not None, data("itemid"), data("liked_count"),
            _getordefault.first_ifn_null([Item.Model(
                model.get("itemid", None), model.get("modelid", None), model.get("name", None),
                model.get("price", None), model.get("stock", None)
            ) for model in data["models"]], data("models")),
            data("name"), data("price"), data("shop_location"),
            data("shopid"), data("stock"), _getordefault.first_ifn_null(Item.UpcomingFlashSale(
                data["upcoming_flash_sale"]("end_time"),
                data["upcoming_flash_sale"]("start_time"),
                data["upcoming_flash_sale"]("stock")
            ), data("upcoming_flash_sale")), data("view_count")
        )

    def add_to_cart(self, item: Item, selected_model: int = 0) -> CartItem:
        if item.stock == 0:
            raise error.CheckoutError("stok item habis")

        resp = self.session.post(_urls.MALL_PREFIX + _urls.PATHS["add_to_cart"],
                                 json={
                                     "quantity": 1,
                                     "donot_add_quality": False,
                                     "client_source": 1,
                                     "shopid": item.shop_id,
                                     "itemid": item.item_id,
                                     "modelid": item.models[selected_model].model_id
                                 })
        data = resp.json()

        if data["error"] != 0:
            print(resp.text)

            raise error.CheckoutError(f"error code: {data['error']}")

        data = data["data"]["cart_item"]

        return CartItem(
            item.add_on_deal_id, str(data["item_group_id"]) if data["item_group_id"]
            is not None else 0, data["itemid"], data["modelid"],
            item.price, item.shop_id
        )

    def checkout(self, item: CartItem, payment: Payment):
        resp = self.session.post(_urls.MALL_PREFIX + _urls.PATHS["checkout"],
                                 data=self.__checkout_get(item, payment))

        try:
            if "error" in resp.json():
                print(resp.text)

                raise error.CheckoutError("checkout error")
            elif resp.status_code == 406:
                print(resp.text)

                raise error.CheckoutError("item mungkin telah habis")
        except ValueError:
            print(resp.status_code)

            raise error.CheckoutError("respon error")

    def __checkout_get(self, item: CartItem, payment: Payment) -> t.Optional[bytes]:
        true, false, null = True, False, None
        resp = self.session.post(_urls.MALL_PREFIX + _urls.PATHS["checkout_get"],
                                 json={
                                     "timestamp": round(time.time()),
                                     "shoporders": [
                                         {
                                             "shop": {
                                                 "shopid": item.shopid
                                             },
                                             "items": [
                                                 {
                                                     "itemid": item.itemid,
                                                     "modelid": item.modelid,
                                                     "add_on_deal_id": item.add_on_deal_id,
                                                     "is_add_on_sub_item": false,
                                                     "item_group_id": item.group_id,
                                                     "quantity": 1
                                                 }
                                             ],
                                             "logistics": {
                                                 "recommended_channelids": null
                                             },
                                             "buyer_address_data": {
                                                 "tax_address": "",
                                                 "address_type": 0,
                                                 "addressid": self.user.address.id_
                                             },
                                             "selected_logistic_channelid": 8003,
                                             "shipping_id": 1,
                                             "selected_preferred_delivery_time_option_id": 0,
                                             "selected_preferred_delivery_time_slot_id": null,
                                             "selected_preferred_delivery_instructions": {
                                                 "0": "",
                                                 "1": "0"
                                             }
                                         }
                                     ],
                                     "selected_payment_channel_data": {
                                         "channel_id": payment.channel_id,
                                         "version": payment.version,
                                         "selected_item_option_info": {
                                             "option_info": payment.option if payment.option is not None else ""
                                         },
                                         "text_info": {}
                                     },
                                     "promotion_data": {
                                         "use_coins": false,
                                         "free_shipping_voucher_info": {
                                             "free_shipping_voucher_id": 0,
                                             "disabled_reason": null,
                                             "free_shipping_voucher_code": ""
                                         },
                                         "platform_vouchers": [],
                                         "shop_vouchers": [],
                                         "check_shop_voucher_entrances": true,
                                         "auto_apply_shop_voucher": false
                                     },
                                     "device_info": {
                                         "device_id": "",
                                         "device_fingerprint": "",
                                         "tongdun_blackbox": "",
                                         "buyer_payment_info": {
                                             "is_jko_app_installed": false
                                         }
                                     },
                                     "cart_type": 0,
                                     "client_id": 0,
                                     "tax_info": {
                                         "tax_id": ""
                                     },
                                     "dropshipping_info": {
                                         "phone_number": "",
                                         "enabled": false,
                                         "name": ""
                                     },
                                     "shipping_orders": [
                                         {
                                             "sync": true,
                                             "logistics": {
                                                 "recommended_channelids": null
                                             },
                                             "buyer_address_data": {
                                                 "tax_address": "",
                                                 "address_type": 0,
                                                 "addressid": self.user.address.id_
                                             },
                                             "selected_logistic_channelid": 8003,
                                             "shipping_id": 1,
                                             "shoporder_indexes": [
                                                 0
                                             ],
                                             "selected_preferred_delivery_time_option_id": 0,
                                             "selected_preferred_delivery_time_slot_id": null,
                                             "selected_preferred_delivery_instructions": {
                                                 "0": "",
                                                 "1": "0"
                                             }
                                         }
                                     ],
                                     "order_update_info": {}
                                 })
        if not resp.ok:
            print(resp.status_code)
            print(resp.text)

            raise error.CheckoutError("error mengambil info checkout")

        return resp.content

from api.models import AmountIngredientInRecipe


def get_list_for_shop(user):
    shopping_list = ["Список покупок"]
    results = {}
    ingredients = AmountIngredientInRecipe.objects.filter(
        recipe__in_cart__user=user
    ).values_list(
        "ingredients__name", "ingredients__measurement_unit", "amount"
    )
    for item in ingredients:
        name = item[0]
        if name not in results:
            results[name] = {"measurement": item[1], "amount": item[2]}
        else:
            results[name]["amount"] += item[2]
    for result in results:
        shopping_list.append(
            f'{result}: {results[result]["amount"]}'
            f'{results[result]["measurement"]}'
        )
    return "\n".join(shopping_list)

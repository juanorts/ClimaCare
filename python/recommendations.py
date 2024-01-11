category1 = "Cold - High Humidity"
category2 = "Moderate AQI"

recommendationStr = []
            
# Day profile 1
if(category1 == "Cold"):
    recommendationStr = ["Llevar una chaqueta aislante de alta calidad para mantenerse abrigado", "Vestir con una capa intermedia entre la camisa y el abrigo", "Cubrir el cuello y cabeza, y usar guantes para las manos"]
elif("Cold - High Humidity" in category1):
    recommendationStr = ["Vestir con una capa con materiales transpirables", "Llevar una capa exterior resistente al agua", "Usar calzado cálido e impermeable"]
elif(category1 == "Hot"):
    recommendationStr = ["Optar por comidas ligeras y ricas en agua, como vegetales y frutas, y evitar platos pesados", "Beber uno o dos litros de agua al día y evitar el alcohol", "Mantener algunas partes de tu cuerpo frescas, como los pies, tobillos, muñecas, la nuca, antebrazos y la sien", "Vestir ropa ligera y de colores claros"]
elif("Hot - High Humidity" in category1):
    recommendationStr = ["Optar por comidas ligeras y ricas en agua, como vegetales y frutas, y evitar platos pesados", "Beber uno o dos litros de agua al día y evitar el alcohol", "Mantener algunas partes de tu cuerpo frescas, como los pies, tobillos, muñecas, la nuca, antebrazos y la sien", "Vestir ropa ligera y de colores claros", "A la hora de hacer ejercicio optar por las partes más frescas del día, temprano en la mañana o al atardecer"]
elif(category1 == "High Humidity"):
    recommendationStr = ["Vestir con una capa con materiales transpirables", "Es crucial mantener una hidratación constante", "A la hora de realizar actividad física optar por áreas bien ventiladas"]

if("Windy" in category1):
    recommendationStr = recommendationStr + ["Usar chaquetas y pantalones fabricados con materiales diseñados para bloquear el viento", "Proteger los ojos con gafas de sol o gafas protectoras"]
elif("Strong Wind" in category1):
    recommendationStr = recommendationStr + ["Usar chaquetas y pantalones fabricados con materiales diseñados para bloquear el viento", "En la calle, mantenterse alejado de cornisas, balcones y evitar áreas con sitios en construcción", "Evitar viajar en motocicleta o bicicleta;Proteger los ojos con gafas de sol o gafas protectoras"]

# Day profile 2
if("High UV" in category2):
    recommendationStr = recommendationStr + ["Al mediodía, mantenerse a la sombra", "Vestir ropa adecuada, un sombrero y gafas de sol", "Usar suficiente protector solar con la protección adecuada para la piel"]
if("Extreme UV" in category2):
    recommendationStr = recommendationStr + ["Tomar precauciones adicionales, la piel no protegida puede dañarse y quemarse rápidamente", "Mantenterse alejado de reflectores de rayos UV como la arena blanca o superficies brillantes", "Usar suficiente protector solar con la protección adecuada para la piel", "Evitar el sol entre las 11:00 y las 16:00"]
if("Low Pressure" in category2):
    recommendationStr = recommendationStr + ["Llevar un paraguas resistente al viento para protegerte de la lluvia", "Extremar las precauciones al conducir, ya que puede haber tormentas", "Si se es sensible a los cambios en la presión atmosférica, tomar precauciones adicionales, llevar los medicamentos necesarios y mantenerse hidratado"]
if("Moderate AQI" in category2):
    recommendationStr = recommendationStr + ["Es seguro participar en actividades al aire libre, pero las personas extremadamente sensibles a la calidad del aire pueden considerar reducir la intensidad y duración de dichas actividades", "Si perteneces a un grupo sensible (como niños pequeños, personas mayores o aquellos con problemas respiratorios o cardíacos), puedes considerar limitar tu tiempo al aire libre"]
if("Unhealthy AQI" in category2):
    recommendationStr = recommendationStr + ["Si se experimentan síntomas como irritación ocular, irritación de garganta, dificultad para respirar o problemas respiratorios, considerar reducir las actividades al aire libre", "El uso de mascarillas protectoras puede ser considerado, especialmente para aquellos sensibles a la calidad del aire"]

for r in recommendationStr:
    print(r)
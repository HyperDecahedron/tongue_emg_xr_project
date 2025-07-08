using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Task1B : MonoBehaviour
{
    [SerializeField] private GameObject taskParent;

    public void Hide() => taskParent.SetActive(false);
    public void Show() => taskParent.SetActive(true);

    public void StartTask()
    {

    }
}

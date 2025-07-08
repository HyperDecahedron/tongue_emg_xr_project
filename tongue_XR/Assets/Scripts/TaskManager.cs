using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class TaskManager : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI startText;
    [SerializeField] private GameObject startPanel;

    [Header("Tasks")]
    [SerializeField] private Task1 task1A;
    [SerializeField] private Task1B task1B;
    [SerializeField] private Task2A task2A;
    [SerializeField] private Task2B task2B;

    private string task = "";

    private void Start()
    {
        startPanel.SetActive(true);
        startText.gameObject.SetActive(false);

        // Hide all tasks initially
        task1A.Hide();
        task1B.Hide();
        task2A.Hide();
        task2B.Hide();
    }

    public void StartTask1A()
    {
        Debug.Log("Starting task 1A");
        task = "1A";
        StartCoroutine(Do321_count());
    }

    public void StartTask1B()
    {
        Debug.Log("Starting task 1B");
        task = "1B";
        StartCoroutine(Do321_count());
    }

    public void StartTask2A()
    {
        Debug.Log("Starting task 2A");
        task = "2A";
        StartCoroutine(Do321_count());
    }

    public void StartTask2B()
    {
        Debug.Log("Starting task 2B");
        task = "2B";
        StartCoroutine(Do321_count());
    }

    private IEnumerator Do321_count()
    {
        startPanel.SetActive(true);
        startText.gameObject.SetActive(true);

        string[] countdown = { "3", "2", "1", "Go!" };

        foreach (string count in countdown)
        {
            startText.text = count;
            yield return new WaitForSeconds(1f);
        }

        startText.gameObject.SetActive(false);
        startPanel.SetActive(false);

        switch (task)
        {
            case "1A":
                task1A.Show();
                task1A.StartTask();
                break;

            case "1B":
                task1B.Show();
                task1B.StartTask();
                break;

            case "2A":
                task2A.Show();
                task2A.StartTask();
                break;

            case "2B":
                task2B.Show();
                task2B.StartTask();
                break;
        }
    }

    public void IntermediatePanel()
    {
        startPanel.SetActive(true);
        startText.gameObject.SetActive(true);
        startText.text = "Wait for the next task.";
    }
}
